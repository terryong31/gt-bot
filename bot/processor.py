"""
Message processor for Telegram bot.
"""

from .config import telegram_agent
from .database import is_user_registered, update_session, log_chat, get_voice_enabled
from .telegram import send_reply, edit_message, get_file_path, download_file, save_media, send_conversational_response
from .handlers import handle_command


def process_message(message):
    """Process a single message - runs in a separate thread"""
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    text = message.get("text", "")
    
    try:
        # Try to handle as command first
        if text.startswith("/"):
            if handle_command(message):
                return
        
        # Check if user is registered and allowed
        is_allowed = is_user_registered(telegram_id)
        
        if is_allowed is None:
            send_reply(chat_id, "❌ You're not registered. Use /start to begin.")
            return
        
        if not is_allowed:
            send_reply(chat_id, "⛔ Your access has been revoked. Please contact your admin.")
            return
        
        # Update activity timestamp (for admin panel tracking)
        update_session(telegram_id)
        
        # Build content list for multimodal input
        contents = []
        message_type = "text"
        saved_file = None
        original_filename = None
        
        # Add text if present
        text_content = message.get("text") or message.get("caption")
        if text_content and not text_content.startswith("/"):
            contents.append(text_content)
        
        # Handle photos (including media groups with multiple photos)
        if "photo" in message:
            message_type = "photo"
            photos = message["photo"]
            
            # Group photos by file_unique_id to get unique photos
            unique_photos = {}
            for p in photos:
                uid = p.get("file_unique_id", p["file_id"])
                if uid not in unique_photos or p.get("file_size", 0) > unique_photos[uid].get("file_size", 0):
                    unique_photos[uid] = p
            
            photo_count = len(unique_photos)
            print(f"[{telegram_id}] Processing {photo_count} photo(s)...")
            
            for photo in unique_photos.values():
                file_path = get_file_path(photo["file_id"])
                if file_path:
                    file_bytes = download_file(file_path)
                    if file_bytes:
                        original_filename = file_path.split('/')[-1]
                        saved_file = save_media(file_bytes, original_filename)
                        ext = file_path.split('.')[-1].lower()
                        if ext == "jpg":
                            ext = "jpeg"
                        mime_type = f"image/{ext}" if ext in ["jpeg", "png", "gif", "webp"] else "image/jpeg"
                        contents.append((file_bytes, mime_type))
        
        # Handle documents
        if "document" in message:
            message_type = "document"
            print(f"[{telegram_id}] Processing document...")
            doc = message["document"]
            file_path = get_file_path(doc["file_id"])
            if file_path:
                file_bytes = download_file(file_path)
                if file_bytes:
                    original_filename = doc.get("file_name", file_path.split('/')[-1])
                    saved_file = save_media(file_bytes, original_filename)
                    mime_type = doc.get("mime_type", "application/octet-stream")
                    contents.append((file_bytes, mime_type))
        
        # Handle audio
        if "audio" in message:
            message_type = "audio"
            print(f"[{telegram_id}] Processing audio...")
            audio = message["audio"]
            file_path = get_file_path(audio["file_id"])
            if file_path:
                file_bytes = download_file(file_path)
                if file_bytes:
                    original_filename = audio.get("file_name", file_path.split('/')[-1])
                    saved_file = save_media(file_bytes, original_filename)
                    mime_type = audio.get("mime_type", "audio/mpeg")
                    contents.append((file_bytes, mime_type))
        
        # Handle voice messages
        if "voice" in message:
            message_type = "voice"
            print(f"[{telegram_id}] Processing voice...")
            voice = message["voice"]
            file_path = get_file_path(voice["file_id"])
            if file_path:
                file_bytes = download_file(file_path)
                if file_bytes:
                    original_filename = file_path.split('/')[-1]
                    saved_file = save_media(file_bytes, original_filename)
                    mime_type = voice.get("mime_type", "audio/ogg")
                    contents.append((file_bytes, mime_type))
        
        # Handle video
        if "video" in message:
            message_type = "video"
            print(f"[{telegram_id}] Processing video...")
            video = message["video"]
            file_path = get_file_path(video["file_id"])
            if file_path:
                file_bytes = download_file(file_path)
                if file_bytes:
                    original_filename = video.get("file_name", file_path.split('/')[-1])
                    saved_file = save_media(file_bytes, original_filename)
                    mime_type = video.get("mime_type", "video/mp4")
                    contents.append((file_bytes, mime_type))
        
        # Process with LangChain agent
        if text_content or saved_file:
            print(f"[{telegram_id}] Processing with LangChain agent...")
            
            # Step 1: Send initial thinking message
            thinking_msg_id = send_reply(chat_id, "🤔 Thinking...")
            last_thinking_text = ""
            
            # Callback to update thinking message in real-time
            def on_thinking_update(thinking_text):
                nonlocal last_thinking_text
                if thinking_text and thinking_text != last_thinking_text:
                    last_thinking_text = thinking_text
                    # Truncate to Telegram limit (4096) with some buffer
                    limit = 3800
                    display_text = f"🤔 Thinking...\n{thinking_text[:limit]}..." if len(thinking_text) > limit else f"🤔 Thinking...\n{thinking_text}"
                    if thinking_msg_id:
                        edit_message(chat_id, thinking_msg_id, display_text)
            
            # Build message for agent with file context
            if saved_file and original_filename:
                file_context = f"User sent a {message_type} file '{original_filename}'"
                if text_content:
                    user_message = f"{file_context} and said: {text_content}"
                else:
                    user_message = file_context
            else:
                user_message = text_content or f"User sent a {message_type} file"
            
            # Collect image, audio, and PDF bytes for multimodal
            image_bytes_list = []
            audio_bytes_list = []
            pdf_bytes_list = []
            
            if contents:
                for content in contents:
                    if isinstance(content, tuple):
                        file_bytes, mime_type = content
                        if mime_type.startswith("image/"):
                            image_bytes_list.append(file_bytes)
                        elif mime_type.startswith("audio/"):
                            audio_bytes_list.append((file_bytes, mime_type))
                        elif mime_type == "application/pdf":
                            pdf_bytes_list.append(file_bytes)
            
            # Store file context for tools to access (documents only, not images/audio)
            if message_type == "document" and saved_file:
                telegram_agent.set_current_file_context(telegram_id, file_bytes, original_filename, mime_type)
            
            # Step 2: Generate response with streaming thinking
            thinking, bot_response = telegram_agent.generate_response_with_thinking(
                user_id=telegram_id,
                message=user_message,
                on_thinking_update=on_thinking_update,
                images=image_bytes_list if image_bytes_list else None,
                audio=audio_bytes_list if audio_bytes_list else None,
                pdfs=pdf_bytes_list if pdf_bytes_list else None
            )
            
            # Step 3: Update thinking message to show it's done (persist full thought)
            if thinking_msg_id:
                limit = 3500
                # Use 'thinking' returned from agent as it is the complete authoritative text
                final_content = thinking if thinking else (last_thinking_text if last_thinking_text else "Done thinking!")
                
                if len(final_content) > limit:
                     final_content = final_content[:limit] + "...\n(Thinking truncated for length)"
                
                final_message = f"✅ Thought Process:\n{final_content}"
                edit_message(chat_id, thinking_msg_id, final_message)

            # Step 4: Send the actual answer using conversational response
            voice_enabled = get_voice_enabled(telegram_id)
            send_conversational_response(chat_id, bot_response, voice_enabled)
            print(f"[{telegram_id}] ✅ Conversational response sent")
            
            # Clear file context after processing
            telegram_agent.clear_current_file_context(telegram_id)
            
            # Log the chat
            log_content = text_content if message_type == "text" else saved_file
            log_chat(telegram_id, message_type, log_content, original_filename, bot_response)
        else:
            print(f"[{telegram_id}] No processable content found")
            
    except Exception as e:
        print(f"[{telegram_id}] Error: {e}")
        import traceback
        traceback.print_exc()
        send_reply(chat_id, f"Sorry, I encountered an error: {str(e)}")
