"""
Gemini Context Caching Manager (Updated for google-genai SDK)
Handles creation and management of explicit context caches.
"""
import os
import datetime
from google import genai
from google.genai import types

class CacheManager:
    def __init__(self, model_name: str = "gemini-1.5-flash-001"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("[Cache] Warning: GEMINI_API_KEY not set. Caching disabled.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            
        self.model_name = model_name
        self._active_cache = None

    def create_cache(
        self, 
        content: list, 
        system_instruction: str = None,
        ttl_minutes: int = 60,
        display_name: str = "telegram_bot_cache"
    ):
        """
        Create a new context cache using the new google-genai SDK.
        """
        try:
            # TTL formatted as string with 's' suffix, e.g. "300s"
            ttl_seconds = ttl_minutes * 60
            ttl = f"{ttl_seconds}s"
            
            # Prepare config
            config = types.CreateCachedContentConfig(
                display_name=display_name,
                system_instruction=system_instruction,
                contents=content, # Expects list of strings or Content objects
                ttl=ttl,
            )
            
            # Create cache
            # Note: The model name usually needs 'models/' prefix or just the version
            # The new SDK is strict.
            model_id = self.model_name
            if not model_id.startswith("models/"):
                model_id = f"models/{model_id}"

            cache = self.client.caches.create(
                model=model_id,
                config=config
            )
            
            self._active_cache = cache
            print(f"[Cache] Created cache: {cache.name}")
            return cache
            
        except Exception as e:
            print(f"[Cache] Error creating cache: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_active_cache(self):
        return self._active_cache

    def clear_cache(self):
        if self._active_cache:
            try:
                self.client.caches.delete(name=self._active_cache.name)
                print(f"[Cache] Deleted cache: {self._active_cache.name}")
                self._active_cache = None
            except Exception as e:
                print(f"[Cache] Error deleting cache: {e}")

# Global instance
cache_manager = CacheManager()
