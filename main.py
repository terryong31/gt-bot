#!/usr/bin/env python3 
"""
GT-Bot - Main Entry Point

This is the main entry point for the GT-Bot.
All business logic is in the bot/ package.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor

from bot import process_message
from bot.telegram import get_updates


def main():
    offset = None
    print("🤖 Bot is running with auth + logging (max 5 workers)...")
    
    executor = ThreadPoolExecutor(max_workers=5)
    
    # Media group batching: {media_group_id: [messages]}
    media_groups = {}
    media_group_timers = {}
    
    def process_media_group(group_id):
        """Process all messages in a media group together."""
        if group_id in media_groups:
            messages = media_groups.pop(group_id)
            media_group_timers.pop(group_id, None)
            if messages:
                # Merge into first message with all photos
                first_msg = messages[0].copy()
                all_photos = []
                for msg in messages:
                    if "photo" in msg:
                        all_photos.extend(msg["photo"])
                if all_photos:
                    first_msg["photo"] = all_photos
                    first_msg["_is_media_group"] = True
                executor.submit(process_message, first_msg)
    
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for item in updates["result"]:
                    offset = item["update_id"] + 1
                    if "message" in item:
                        msg = item["message"]
                        media_group_id = msg.get("media_group_id")
                        
                        if media_group_id:
                            # Part of a media group - batch it
                            if media_group_id not in media_groups:
                                media_groups[media_group_id] = []
                            media_groups[media_group_id].append(msg)
                            
                            # Process after 0.5s of no new messages in this group
                            if media_group_id in media_group_timers:
                                media_group_timers[media_group_id].cancel()
                            timer = threading.Timer(0.5, process_media_group, [media_group_id])
                            media_group_timers[media_group_id] = timer
                            timer.start()
                        else:
                            # Single message - process immediately
                            executor.submit(process_message, msg)
        except Exception as e:
            print(f"[Main] Polling error: {e}")
            time.sleep(1)
                        
        time.sleep(0.1)


if __name__ == "__main__":
    main()