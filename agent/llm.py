"""
LangChain LLM wrapper for Gemini with tool execution and streaming thinking.
Streams tokens in real-time and executes tools when the model requests them.
"""
import os
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage

from .memory import memory_manager
from .tool_memory import ToolSessionMemory


@dataclass
class AgentConfig:
    """Configuration for the LangChain agent."""
    model: str = "gemini-3-flash-preview"
    temperature: float = 0.7
    enable_search: bool = True
    enable_memory: bool = True
    max_tokens: Optional[int] = None
    system_prompt: str = """You are a helpful AI assistant in a Telegram chat. 
Be concise and helpful. If you search the web, cite your sources with URLs at the end.
Reply in plaintext format, do not use markdown format and only use linebreaks when necessary. 
If you receive a document like images, pdf files and etc. Return your findings in json format.
Keep your answers short and simple.

CRITICAL FILE HANDLING:
When a user sends you a file (PDF, DOCX, etc.) WITH instructions in the same message:
- The file is ALREADY uploaded and available to you
- DO NOT ask the user to upload it again
- DO NOT ask for the file name (you already have it)
- USE the appropriate tool to process the file immediately
- For PDFs with "catalogue" or "save": use save_catalogue tool
- For DOCX with "template" or "quotation": use upload_and_set_quotation_template tool

CRITICAL: FOLLOW USER INSTRUCTIONS PRECISELY:
When user asks you to create a folder and save files inside:
1. Use create_drive_folder to create the folder FIRST
2. Then save files to that folder using the folder_name parameter
3. DO NOT skip folder creation - if user says "create folder X", create it!
4. When saving catalogues: use save_catalogue(catalogue_name="...", folder_name="...")
5. Name files sensibly - don't use redundant names

CRITICAL: ERROR HANDLING AND EFFICIENCY:
- If a tool returns an error (503, timeout, etc.), DO NOT immediately retry the SAME tool with SAME parameters
- Tell the user about the error and suggest waiting a moment before trying again
- Do NOT waste iterations retrying failed operations - give a clear response instead
- If "multiple documents found", ask user to specify - don't blindly try again
- Be EFFICIENT: complete tasks in as FEW iterations as possible

CRITICAL: LEARN FROM SESSION CONTEXT:
- Check the SESSION CONTEXT section for operations that already failed
- DO NOT retry operations that are marked as failed
- If a search returned "no items found", don't search for variations of the same term
- Use alternative approaches instead of repeating failures

You have access to Google tools (Gmail, Drive, Sheets). When the user asks about their Google account, 
USE the tools to get real data - don't make things up.

CRITICAL: You MUST process the user's request step-by-step inside <thinking></thinking> tags before answering.
Inside the tags, describe your thought process. 
"""


class TelegramAgent:
    """LangChain agent for Telegram with real-time streaming and tool execution."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize model with streaming
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.model,
            google_api_key=self.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            convert_system_message_to_human=True,
            streaming=True,
        )
        
        # Note: Tools are bound per-request in _get_llm_with_user_tools()
        # to support per-user Google API credentials
        
        # Conversation history per user
        self.conversations: Dict[int, List[Any]] = {}
        
        # File context storage: {user_id: (file_bytes, filename, mime_type)}
        self.current_file_context: Dict[int, tuple] = {}
        
        # Tool session memory per user - tracks failed/successful calls within a session
        self.tool_sessions: Dict[int, ToolSessionMemory] = {}
    
    def get_history(self, user_id: int) -> List[Any]:
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def add_to_history(self, user_id: int, role: str, content: str):
        history = self.get_history(user_id)
        if role == "user":
            history.append(HumanMessage(content=content))
        else:
            history.append(AIMessage(content=content))
        if len(history) > 20:
            self.conversations[user_id] = history[-20:]
    
    def clear_history(self, user_id: int):
        self.conversations[user_id] = []
    
    def set_current_file_context(self, user_id: int, file_bytes: bytes, filename: str, mime_type: str):
        """Store file context for the current message processing."""
        self.current_file_context[user_id] = (file_bytes, filename, mime_type)
    
    def get_current_file_context(self, user_id: int) -> Optional[tuple]:
        """Get file context for the current message."""
        return self.current_file_context.get(user_id)
    
    def clear_current_file_context(self, user_id: int):
        """Clear file context after processing."""
        if user_id in self.current_file_context:
            del self.current_file_context[user_id]
    
    def clear_tool_session(self, user_id: int):
        """Clear tool session memory after request completes."""
        if user_id in self.tool_sessions:
            self.tool_sessions[user_id].clear()
    
    def _get_tools_for_user(self, user_id: int) -> List[Any]:
        """Get tools for a specific user. Always returns at least the connection check tool."""
        try:
            from .google_tools import get_google_tools
            
            # ALWAYS get tools - get_google_tools now includes connection check tool
            # regardless of whether user has Google credentials
            tools = get_google_tools(user_id)
            if tools:
                print(f"[LLM] Got {len(tools)} tools for user {user_id}")
                return tools
        except Exception as e:
            print(f"[LLM] Error loading tools: {e}")
            import traceback
            traceback.print_exc()
        return []
    
    def generate_response_with_thinking(
        self,
        user_id: int,
        message: str,
        on_thinking_update: Optional[Callable[[str], None]] = None,
        images: Optional[List[bytes]] = None,
        audio: Optional[List[tuple[bytes, str]]] = None,  # List of (bytes, mime_type)
        pdfs: Optional[List[bytes]] = None  # List of PDF bytes
    ) -> tuple[str, str]:
        """
        Generate response with tool execution and thinking display.
        Returns (thinking_content, answer_content).
        """
        # Get user's tools
        tools = self._get_tools_for_user(user_id)
        
        # Bind tools if available
        if tools:
            llm_with_tools = self.llm.bind_tools(tools)
            tool_names = [t.name for t in tools]
            print(f"[LLM] Bound {len(tools)} tools: {tool_names}")
        else:
            llm_with_tools = self.llm
            print(f"[LLM] No tools bound")
        
        # Get memory context (semantic search)
        memory_context = ""
        if self.config.enable_memory:
            memory_context = memory_manager.get_context(user_id, message, n_results=5)
        
        # Get persistent memory context (permanent user profile)
        from .persistent_memory import get_user_memory_context, process_message_for_memory
        persistent_context = get_user_memory_context(user_id)
        
        # Process message for potential memory triggers (async-like, store for later)
        if isinstance(message, str) and len(message) > 10:
            remembered = process_message_for_memory(user_id, message)
            if remembered:
                print(f"[LLM] Remembered: {remembered}")
        
        # Build system prompt
        system_content = self.config.system_prompt
        
        # Performance Optimization: Conditional Thinking
        # Skip excessive thinking for simple queries (less than 10 chars or simple greetings)
        is_simple_query = False
        if isinstance(message, str) and (len(message.strip()) < 10 or message.lower().strip() in ['hi', 'hello', 'hey', 'start']):
            is_simple_query = True
            # Replace the strict thinking requirement with a lighter instruction
            system_content = system_content.replace(
                "CRITICAL: CHAIN OF THOUGHT\nYou MUST think before you speak. Every response must strictly follow this format:",
                "For this simple request, reply directly without thinking tags."
            ).replace(
                "<thinking>\n1. Analyze the user's request.\n2. Check if any tools (Gmail, Drive, Memory, etc.) are needed.\n3. Formulate the execution plan.\n4. Construct the final response.\n</thinking>",
                ""
            )
        
        # Add persistent memory context first (most important)
        if persistent_context:
            system_content += f"\n\n{persistent_context}"
        
        # Add semantic memory context
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        # Build messages
        messages = [SystemMessage(content=system_content)]
        messages.extend(self.get_history(user_id))
        
        
        # Handle multimodal content (images, audio, and PDFs)
        if images or audio or pdfs:
            import base64
            content = [{"type": "text", "text": message}]
            
            # Add images
            if images:
                for img_bytes in images:
                    b64 = base64.b64encode(img_bytes).decode()
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
            
            # Add audio
            if audio:
                for audio_bytes, mime_type in audio:
                    b64 = base64.b64encode(audio_bytes).decode()
                    # Gemini expects inline data for audio
                    content.append({
                        "type": "media",
                        "mime_type": mime_type,
                        "data": b64
                    })
            
            # Add PDFs
            if pdfs:
                for pdf_bytes in pdfs:
                    b64 = base64.b64encode(pdf_bytes).decode()
                    content.append({
                        "type": "media",
                        "mime_type": "application/pdf",
                        "data": b64
                    })
                    
            messages.append(HumanMessage(content=content))
        else:
            messages.append(HumanMessage(content=message))
        
        try:
            # Tool execution loop (max iterations to handle complex multi-tool queries)
            max_iterations = 15  # Reduced from 20 since we're smarter now
            iteration = 0
            final_response = ""
            thinking_content = ""
            chart_files = []  # Track chart files from tool results
            
            # Initialize or get session memory for this user
            if user_id not in self.tool_sessions:
                self.tool_sessions[user_id] = ToolSessionMemory()
            session_memory = self.tool_sessions[user_id]
            
            while iteration < max_iterations:
                iteration += 1
                print(f"[LLM] Iteration {iteration}")
                
                # Inject session context if we have failures (after first iteration)
                if iteration > 1:
                    session_context = session_memory.get_context_summary()
                    if session_context:
                        # Update the system message with session context
                        context_message = f"\n\nSESSION CONTEXT (Learn from previous attempts):\n{session_context}\n\nDO NOT repeat failed operations. Use alternative approaches or inform the user."
                        if messages and isinstance(messages[0], SystemMessage):
                            messages[0] = SystemMessage(content=messages[0].content + context_message)
                
                # Invoke the model (not stream for tool calls)
                response = llm_with_tools.invoke(messages)
                
                # Check if model wants to call tools
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"[LLM] Model requested {len(response.tool_calls)} tool calls")
                    
                    # Add assistant message with tool calls
                    messages.append(response)
                    
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        print(f"[LLM] Calling tool: {tool_name} with args: {tool_args}")
                        
                        # NEW: Check if similar call already failed
                        failure_reason = session_memory.has_similar_failure(tool_name, tool_args)
                        if failure_reason:
                            tool_result = f"⚠️ SKIPPED (similar attempt already failed): {failure_reason}. Try a different approach."
                            print(f"[LLM] Skipping tool (similar failure): {failure_reason}")
                        else:
                            # Find and execute the tool
                            tool_result = "Tool not found"
                            tool_success = False
                            
                            for tool in tools:
                                if tool.name == tool_name:
                                    try:
                                        tool_result = tool.invoke(tool_args)
                                        print(f"[LLM] Tool result: {str(tool_result)[:200]}...")
                                        
                                        # Determine success based on result content
                                        result_str = str(tool_result).lower()
                                        tool_success = not any(x in result_str for x in [
                                            "❌", "error", "not found", "no items found", 
                                            "no files found", "failed", "timeout", "503"
                                        ])
                                        
                                        # Capture chart files from tool results
                                        if "CHART_FILE:" in str(tool_result):
                                            import re
                                            chart_matches = re.findall(r'CHART_FILE:([^\s]+)', str(tool_result))
                                            chart_files.extend(chart_matches)
                                            print(f"[LLM] Captured chart files: {chart_matches}")
                                            
                                    except Exception as e:
                                        tool_result = f"Error executing tool: {str(e)}"
                                        tool_success = False
                                        print(f"[LLM] Tool error: {e}")
                                    break
                            
                            # NEW: Record the tool call result
                            session_memory.record_call(tool_name, tool_args, str(tool_result), tool_success)
                        
                        # Add tool result to messages
                        messages.append(ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call['id']
                        ))
                    
                    # Continue loop to get final response
                    continue
                else:
                    # No tool calls - this is the final response
                    raw_content = response.content if hasattr(response, 'content') else str(response)
                    print(f"[LLM] Raw response type: {type(raw_content)}, content: {str(raw_content)[:200]}")
                    
                    # Handle case where content is a list
                    if isinstance(raw_content, list):
                        final_response = "".join(
                            block if isinstance(block, str) else block.get('text', '') 
                            for block in raw_content if isinstance(block, (str, dict))
                        )
                    else:
                        final_response = str(raw_content)
                    print(f"[LLM] Got final response: {len(final_response)} chars")
                    break
            
            # Parse thinking from response
            if final_response:
                thinking_start = final_response.find("<thinking>")
                thinking_end = final_response.find("</thinking>")
                
                if thinking_start != -1 and thinking_end != -1:
                    thinking_content = final_response[thinking_start + 10:thinking_end]
                    answer_content = final_response[thinking_end + 11:].strip()
                else:
                    thinking_content = ""
                    answer_content = final_response
                
                # Ensure we have an answer
                if not answer_content:
                    answer_content = thinking_content if thinking_content else final_response
                
                # Note: Chart files are appended AFTER this block to avoid duplication
                
                # Update thinking callback
                if on_thinking_update and thinking_content:
                    on_thinking_update(thinking_content)
            else:
                thinking_content = ""
                answer_content = ""
                
            # ALWAYS append chart files if we have them (even if LLM gave no text)
            if chart_files:
                print(f"[LLM] Appending {len(chart_files)} chart files to response")
                chart_markers = " ".join([f"CHART_FILE:{path}" for path in chart_files])
                if answer_content:
                    answer_content = f"{chart_markers}\n\n{answer_content}"
                else:
                    answer_content = f"{chart_markers}\n\nHere's the chart you requested."
            elif not answer_content:
                answer_content = "I apologize, but I couldn't generate a response. Please try again."
            
            # Add to histories
            self.add_to_history(user_id, "user", message)
            self.add_to_history(user_id, "assistant", answer_content)
            
            # Store in memory
            if self.config.enable_memory:
                memory_manager.add_conversation(user_id, message, answer_content)
            
            return thinking_content, answer_content
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[LLM] {error_msg}")
            import traceback
            traceback.print_exc()
            return "Error", error_msg

    # Backward compatibility
    def generate_response(
        self,
        user_id: int,
        message: str,
        images: Optional[List[bytes]] = None,
    ) -> str:
        """Generate response (returns only the answer)."""
        _, answer = self.generate_response_with_thinking(user_id, message, None, images)
        return answer


def create_agent(config: Optional[AgentConfig] = None) -> TelegramAgent:
    return TelegramAgent(config)
