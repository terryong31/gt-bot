"""
Telegram API helpers - Send messages, voice, files, etc.
"""

import os
import uuid
import requests
import subprocess

from .config import TOKEN, base_url, file_url, UPLOADS_DIR, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"{base_url}/getUpdates"
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset
    
    response = requests.get(url, params=params)
    return response.json()


def send_reply(chat_id, text, parse_mode=None):
    """Sends a message back to the specific chat_id, returns message_id"""
    url = f"{base_url}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    response = requests.post(url, json=payload)
    data = response.json()
    if data.get("ok"):
        return data["result"]["message_id"]
    return None


def send_voice_reply(chat_id, text):
    """Convert text to speech using ElevenLabs and send as voice message (OGG format)"""
    if not ELEVENLABS_API_KEY:
        print("[Voice] ElevenLabs API key not set, falling back to text")
        return send_reply(chat_id, text)
    
    try:
        # ElevenLabs API - request OGG format directly (Telegram compatible)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[Voice] ElevenLabs error: {response.status_code} - {response.text[:100]}")
            return send_reply(chat_id, text)
        
        # Save audio file temporarily
        audio_path = f"/tmp/voice_{uuid.uuid4()}.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        # Convert MP3 to OGG using ffmpeg (Telegram requires OGG for voice)
        ogg_path = f"/tmp/voice_{uuid.uuid4()}.ogg"
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-c:a", "libopus", "-b:a", "64k", ogg_path],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"[Voice] FFmpeg error: {result.stderr.decode()[:100]}")
            os.remove(audio_path)
            return send_reply(chat_id, text)
        
        # Send voice message
        voice_url = f"{base_url}/sendVoice"
        with open(ogg_path, "rb") as voice_file:
            response = requests.post(
                voice_url,
                data={"chat_id": chat_id},
                files={"voice": voice_file}
            )
        
        # Cleanup
        os.remove(audio_path)
        os.remove(ogg_path)
        
        data = response.json()
        if data.get("ok"):
            return data["result"]["message_id"]
        else:
            print(f"[Voice] Telegram error: {data}")
            return send_reply(chat_id, text)
            
    except Exception as e:
        print(f"[Voice] Error: {e}")
        import traceback
        traceback.print_exc()
        return send_reply(chat_id, text)


def edit_message(chat_id, message_id, text):
    """Edits an existing message"""
    url = f"{base_url}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }
    requests.post(url, json=payload)


def get_file_path(file_id):
    """Get the file path from Telegram for a given file_id"""
    url = f"{base_url}/getFile"
    params = {"file_id": file_id}
    response = requests.get(url, params=params)
    result = response.json()
    if result.get("ok"):
        return result["result"]["file_path"]
    return None


def download_file(file_path):
    """Download a file from Telegram servers and return the bytes"""
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None


def save_media(file_bytes, original_name):
    """Save media file and return filename. Converts HEIC to JPEG."""
    ext = original_name.split('.')[-1].lower() if '.' in original_name else 'bin'
    
    # Handle HEIC files (iPhone format)
    if ext in ['heic', 'heif']:
        try:
            from pillow_heif import register_heif_opener
            from PIL import Image
            import io
            
            # Register HEIF opener with Pillow
            register_heif_opener()
            
            # Convert HEIC to JPEG
            image = Image.open(io.BytesIO(file_bytes))
            output = io.BytesIO()
            image.convert('RGB').save(output, format='JPEG', quality=90)
            file_bytes = output.getvalue()
            ext = 'jpg'
            print(f"Converted HEIC image to JPEG")
        except Exception as e:
            print(f"Failed to convert HEIC: {e}, saving as-is")
    
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(file_bytes)
    return filename


def send_photo(chat_id, photo_path, caption=None):
    """Send a photo to the chat"""
    url = f"{base_url}/sendPhoto"
    
    with open(photo_path, "rb") as photo_file:
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        response = requests.post(url, data=data, files={"photo": photo_file})
    
    result = response.json()
    if result.get("ok"):
        return result["result"]["message_id"]
    else:
        print(f"[Telegram] Error sending photo: {result}")
    return None


def should_use_voice(message: str, voice_enabled: bool) -> bool:
    """
    Determine if a message should be sent as voice.
    Only uses voice for short ENGLISH conversational bits without important data.
    """
    import re
    
    if not voice_enabled:
        return False
    
    # Never voice if contains important searchable data
    # Check for currency/numbers
    has_currency = bool(re.search(r'\$[\d,]+', message))
    has_numbers = bool(re.search(r'\b\d+[\d,]*\.?\d*\b', message))
    
    # Check for names/proper nouns (capitalized words not at start)
    words = message.split()
    has_names = any(
        word[0].isupper() and i > 0 
        for i, word in enumerate(words) 
        if word and word[0].isalpha()
    )
    
    # Check for lists
    is_list = message.count('\n') > 1 or '•' in message or message.count(':') > 1
    
    # Skip voice for data-heavy messages
    if has_currency or (has_numbers and len(words) < 20) or is_list:
        return False
    
    # LANGUAGE DETECTION - Only voice for predominantly English/Latin text
    # Check for CJK characters (Chinese, Japanese, Korean)
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')
    cjk_chars = len(cjk_pattern.findall(message))
    
    # Check for other non-Latin scripts (Arabic, Hebrew, Thai, etc.)
    non_latin_pattern = re.compile(r'[\u0600-\u06ff\u0590-\u05ff\u0e00-\u0e7f\u0400-\u04ff]')
    non_latin_chars = len(non_latin_pattern.findall(message))
    
    # If more than 10% of text is non-Latin, skip voice
    total_chars = len(message.replace(' ', ''))
    if total_chars > 0:
        non_latin_ratio = (cjk_chars + non_latin_chars) / total_chars
        if non_latin_ratio > 0.1:
            return False
    
    # Only voice very short conversational bits (15 words max for English)
    # For languages with spaces, count words
    word_count = len(words)
    return word_count <= 15


def split_into_chunks(text: str) -> list:
    """
    Split text into conversational message chunks.
    Keeps related content together, splits at natural breaks.
    """
    chunks = []
    
    # First split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If paragraph is short enough, keep it together
        if len(para) <= 200:
            chunks.append(para)
        else:
            # Split long paragraphs at sentence boundaries
            sentences = []
            current = ""
            
            for char in para:
                current += char
                if char in '.!?' and len(current) > 30:
                    sentences.append(current.strip())
                    current = ""
            
            if current.strip():
                sentences.append(current.strip())
            
            # Group sentences into chunks of 2-3
            chunk = ""
            for sentence in sentences:
                if len(chunk) + len(sentence) < 250:
                    chunk += (" " if chunk else "") + sentence
                else:
                    if chunk:
                        chunks.append(chunk)
                    chunk = sentence
            
            if chunk:
                chunks.append(chunk)
    
    return chunks if chunks else [text]


def send_conversational_response(chat_id: int, response: str, voice_enabled: bool = False, images: list = None):
    """
    Send response as multiple messages like a professional assistant.
    - Splits long text into digestible chunks
    - Sends images inline
    - Uses voice strategically for short non-data messages
    """
    import time
    
    # Handle chart images first
    if images:
        for img_path in images:
            if os.path.exists(img_path):
                print(f"[Telegram] Sending image: {img_path}")
                send_photo(chat_id, img_path)
                time.sleep(0.3)
            else:
                print(f"[Telegram] Image not found: {img_path}")
    
    # Check if response contains a chart file path
    if "CHART_FILE:" in response:
        import re
        chart_matches = re.findall(r'CHART_FILE:([^\s]+)', response)
        # Deduplicate chart paths while preserving order
        seen = set()
        chart_matches = [x for x in chart_matches if not (x in seen or seen.add(x))]
        print(f"[Telegram] Found chart markers (deduplicated): {chart_matches}")
        
        for chart_path in chart_matches:
            chart_path = chart_path.strip()
            print(f"[Telegram] Checking chart path: {chart_path}")
            
            if os.path.exists(chart_path):
                print(f"[Telegram] Sending chart: {chart_path}")
                result = send_photo(chat_id, chart_path)
                if result:
                    print(f"[Telegram] Chart sent successfully")
                else:
                    print(f"[Telegram] Failed to send chart")
                time.sleep(0.3)
            else:
                print(f"[Telegram] Chart file not found: {chart_path}")
                # Try to send error message
                send_reply(chat_id, f"📊 Chart was generated but couldn't be sent (file not accessible)")
        
        # Remove chart file markers from response
        response = re.sub(r'CHART_FILE:[^\s]+\s*', '', response).strip()
    
    # Skip if response is empty after removing chart markers
    if not response.strip():
        return
    
    # Split response into chunks
    chunks = split_into_chunks(response)
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        
        # Decide voice or text
        use_voice = should_use_voice(chunk, voice_enabled)
        
        if use_voice:
            send_voice_reply(chat_id, chunk)
        else:
            send_reply(chat_id, chunk)
        
        # Small delay between messages for natural feel
        if i < len(chunks) - 1:
            time.sleep(0.4)

