"""
Persistent Memory System - Long-term user memory like ChatGPT.
Stores user identity, preferences, and explicit facts in SQLite.
Automatically detects when to remember information.
"""

import sqlite3
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from bot.config import DATABASE_PATH


class PersistentUserMemory:
    """
    Manages permanent user facts stored in SQLite.
    This is for data that should NEVER be forgotten:
    - User identity (name, company, role)
    - Preferences (folders, templates, settings)
    - Explicit requests ("Remember that...")
    """
    
    # Memory categories
    CATEGORY_IDENTITY = "identity"      # name, company, email, role
    CATEGORY_PREFERENCE = "preference"  # quotation folder, template, etc.
    CATEGORY_FACT = "fact"              # explicit "remember that" requests
    CATEGORY_LEARNED = "learned"        # inferred from behavior
    
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id
    
    def get_user_profile(self) -> Dict[str, str]:
        """Get all stored info about the user."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, key, value FROM user_persistent_memory
            WHERE telegram_id = ?
            ORDER BY category, key
        """, (self.telegram_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        profile = {}
        for category, key, value in rows:
            if category not in profile:
                profile[category] = {}
            profile[category][key] = value
        
        return profile
    
    def get_value(self, category: str, key: str) -> Optional[str]:
        """Get a specific stored value."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value FROM user_persistent_memory
            WHERE telegram_id = ? AND category = ? AND key = ?
        """, (self.telegram_id, category, key))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def set_value(self, category: str, key: str, value: str):
        """Store or update a value."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_persistent_memory (telegram_id, category, key, value, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(telegram_id, category, key) 
            DO UPDATE SET value = excluded.value, updated_at = datetime('now')
        """, (self.telegram_id, category, key, value))
        
        conn.commit()
        conn.close()
        print(f"[PersistentMemory] Stored: {category}/{key} = {value[:50]}...")
    
    def remember_fact(self, fact: str, key: Optional[str] = None):
        """Store an explicit fact the user asked to remember."""
        if not key:
            # Generate key from first few words
            key = "_".join(fact.split()[:5]).lower()[:50]
        self.set_value(self.CATEGORY_FACT, key, fact)
    
    def forget(self, category: str, key: str) -> bool:
        """Remove a stored memory."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM user_persistent_memory
            WHERE telegram_id = ? AND category = ? AND key = ?
        """, (self.telegram_id, category, key))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_all(self):
        """Clear all memories for this user."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_persistent_memory WHERE telegram_id = ?", (self.telegram_id,))
        conn.commit()
        conn.close()
    
    def get_context_prompt(self) -> str:
        """Generate context string to inject into system prompt."""
        profile = self.get_user_profile()
        
        if not profile:
            return ""
        
        parts = ["📋 USER PROFILE (Permanent Memory):"]
        
        # Identity info
        if self.CATEGORY_IDENTITY in profile:
            identity = profile[self.CATEGORY_IDENTITY]
            if "name" in identity:
                parts.append(f"  • Name: {identity['name']}")
            if "company" in identity:
                parts.append(f"  • Company: {identity['company']}")
            if "email" in identity:
                parts.append(f"  • Email: {identity['email']}")
            if "role" in identity:
                parts.append(f"  • Role: {identity['role']}")
        
        # Preferences
        if self.CATEGORY_PREFERENCE in profile:
            prefs = profile[self.CATEGORY_PREFERENCE]
            parts.append("  Preferences:")
            for key, value in list(prefs.items())[:5]:  # Limit to 5
                parts.append(f"    - {key}: {value}")
        
        # Facts
        if self.CATEGORY_FACT in profile:
            facts = profile[self.CATEGORY_FACT]
            parts.append("  Remember:")
            for key, value in list(facts.items())[:5]:  # Limit to 5
                parts.append(f"    - {value}")
        
        return "\n".join(parts)


def detect_memory_triggers(message: str) -> List[Tuple[str, str, str]]:
    """
    Detect if a message contains triggers that should be persisted.
    Returns list of (category, key, value) tuples.
    
    ChatGPT-style triggers:
    - "My name is X" → identity/name
    - "I work at X" / "I'm at X company" → identity/company
    - "Remember that X" / "Don't forget X" → fact
    - "Always X" / "I prefer X" / "I like X" → preference
    - "Call me X" → identity/nickname
    """
    triggers = []
    msg_lower = message.lower()
    
    # Identity patterns
    name_patterns = [
        r"my name is (\w+(?:\s+\w+)?)",
        r"i[''`]m (\w+)(?:\s|,|\.)",
        r"call me (\w+)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            name = match.group(1).strip().title()
            triggers.append(("identity", "name", name))
            break
    
    # Company patterns
    company_patterns = [
        r"i work (?:at|for) ([^,.]+)",
        r"i[''`]m (?:at|from|with) ([^,.]+?)(?:\s+company|\s+inc|\s+ltd)?[,.]",
        r"my company is ([^,.]+)",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            company = match.group(1).strip().title()
            if len(company) > 2:  # Avoid false positives
                triggers.append(("identity", "company", company))
                break
    
    # Email patterns
    email_match = re.search(r"my email is ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", message)
    if email_match:
        triggers.append(("identity", "email", email_match.group(1)))
    
    # Explicit remember patterns
    remember_patterns = [
        r"remember (?:that )?(.{10,100})",
        r"don[''`]t forget (?:that )?(.{10,100})",
        r"keep in mind (?:that )?(.{10,100})",
        r"note (?:that )?(.{10,100})",
    ]
    for pattern in remember_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            fact = match.group(1).strip()
            key = "_".join(fact.split()[:4])[:30]
            triggers.append(("fact", key, fact))
            break
    
    # Preference patterns
    preference_patterns = [
        (r"i (?:always |usually )?prefer (.{5,50})", "preference"),
        (r"always (.{5,50})", "always"),
        (r"i like (?:to |when )?(.{5,50})", "likes"),
    ]
    for pattern, pref_key in preference_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            value = match.group(1).strip()
            triggers.append(("preference", pref_key, value))
            break
    
    return triggers


def process_message_for_memory(telegram_id: int, message: str) -> List[str]:
    """
    Process a message and store any detected persistent memories.
    Returns list of what was remembered.
    """
    triggers = detect_memory_triggers(message)
    
    if not triggers:
        return []
    
    memory = PersistentUserMemory(telegram_id)
    remembered = []
    
    for category, key, value in triggers:
        memory.set_value(category, key, value)
        remembered.append(f"{category}/{key}: {value}")
    
    return remembered


def get_user_memory_context(telegram_id: int) -> str:
    """Get the persistent memory context for a user's system prompt."""
    memory = PersistentUserMemory(telegram_id)
    return memory.get_context_prompt()
