"""
Tool Session Memory - Tracks tool calls within a session to prevent redundant calls.
Implements learning from failures and context injection for smarter agent behavior.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import re


@dataclass
class ToolCall:
    """Record of a single tool call."""
    tool_name: str
    args: Dict[str, Any]
    result: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "tool": self.tool_name,
            "args": self.args,
            "success": self.success,
            "result_preview": self.result[:100] if self.result else ""
        }


class ToolSessionMemory:
    """
    Track tool calls within a single user session to prevent redundant calls
    and enable learning from failures.
    """
    
    def __init__(self):
        self.calls: List[ToolCall] = []
        self.failed_patterns: Dict[str, str] = {}  # Pattern key → failure reason
        
    def record_call(self, tool_name: str, args: dict, result: str, success: bool):
        """Record a tool call and its result."""
        call = ToolCall(
            tool_name=tool_name,
            args=args,
            result=result,
            success=success
        )
        self.calls.append(call)
        
        # Track failure patterns for common tools
        if not success:
            pattern_key = self._get_pattern_key(tool_name, args)
            self.failed_patterns[pattern_key] = self._extract_failure_reason(result)
    
    def _get_pattern_key(self, tool_name: str, args: dict) -> str:
        """Generate a pattern key for similarity matching."""
        # For search operations, normalize the query
        if tool_name in ["search_catalogue", "search_drive_files", "search_gmail"]:
            query = args.get("query", args.get("search_term", "")).lower().strip()
            return f"{tool_name}:{query}"
        
        # For other operations, use tool name + key args
        key_args = json.dumps(args, sort_keys=True)
        return f"{tool_name}:{key_args}"
    
    def _extract_failure_reason(self, result: str) -> str:
        """Extract a concise failure reason from the result."""
        if "No items found" in result:
            return "No items found in catalogues"
        if "No files found" in result:
            return "No files found in Drive"
        if "not found" in result.lower():
            return "Resource not found"
        if "multiple" in result.lower():
            return "Multiple matches found - need clarification"
        if "timeout" in result.lower():
            return "API timeout"
        if "503" in result or "Service Unavailable" in result:
            return "API temporarily unavailable"
        return result[:50] if result else "Unknown error"
    
    def has_similar_failure(self, tool_name: str, args: dict) -> Optional[str]:
        """
        Check if a similar call already failed. 
        Returns failure reason if found, None otherwise.
        """
        pattern_key = self._get_pattern_key(tool_name, args)
        
        # Exact match
        if pattern_key in self.failed_patterns:
            return self.failed_patterns[pattern_key]
        
        # For search operations, check for semantic similarity
        if tool_name in ["search_catalogue", "search_drive_files"]:
            query = args.get("query", args.get("search_term", "")).lower().strip()
            
            # Check if we've already tried similar searches
            for failed_key, reason in self.failed_patterns.items():
                if not failed_key.startswith(f"{tool_name}:"):
                    continue
                    
                failed_query = failed_key.split(":", 1)[1]
                
                # Check if queries are variations of each other
                if self._is_search_variation(query, failed_query):
                    return f"Similar search already failed: '{failed_query}' → {reason}"
        
        return None
    
    def _is_search_variation(self, query1: str, query2: str) -> bool:
        """Check if two search queries are variations of each other."""
        # Remove common words and compare
        stopwords = {"the", "a", "an", "for", "in", "on", "with"}
        
        words1 = set(query1.lower().split()) - stopwords
        words2 = set(query2.lower().split()) - stopwords
        
        # If one query is a subset of another
        if words1 and words2:
            if words1.issubset(words2) or words2.issubset(words1):
                return True
            
            # If significant overlap (>50% common words)
            common = words1 & words2
            total = words1 | words2
            if total and len(common) / len(total) > 0.5:
                return True
        
        return False
    
    def get_context_summary(self) -> str:
        """Generate a summary of the session for LLM context injection."""
        if not self.calls:
            return ""
        
        summary_parts = []
        
        # Summarize failures
        if self.failed_patterns:
            summary_parts.append("⚠️ FAILED OPERATIONS (do NOT retry):")
            for pattern, reason in list(self.failed_patterns.items())[:5]:
                tool, detail = pattern.split(":", 1) if ":" in pattern else (pattern, "")
                summary_parts.append(f"  - {tool}: {reason}")
        
        # Note successful operations
        successes = [c for c in self.calls if c.success]
        if successes:
            recent = successes[-3:]  # Last 3 successes
            summary_parts.append("\n✅ SUCCESSFUL OPERATIONS:")
            for call in recent:
                summary_parts.append(f"  - {call.tool_name}: worked")
        
        return "\n".join(summary_parts)
    
    def get_failure_count(self, tool_name: str) -> int:
        """Count how many times a specific tool has failed."""
        return sum(1 for c in self.calls if c.tool_name == tool_name and not c.success)
    
    def should_skip_tool(self, tool_name: str) -> tuple[bool, str]:
        """
        Determine if a tool should be skipped entirely based on failure history.
        Returns (should_skip, reason).
        """
        failure_count = self.get_failure_count(tool_name)
        
        # If a tool has failed 3+ times, suggest skipping
        if failure_count >= 3:
            return True, f"Tool '{tool_name}' has failed {failure_count} times this session"
        
        return False, ""
    
    def clear(self):
        """Clear the session memory."""
        self.calls.clear()
        self.failed_patterns.clear()
