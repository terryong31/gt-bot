"""
Memory Tools - Allow users to view and manage their persistent memories.
"""

from typing import Optional
from langchain_core.tools import tool


def get_memory_tools(telegram_id: int) -> list:
    """Get memory management tools for a user."""
    
    from .persistent_memory import PersistentUserMemory
    
    @tool
    def view_my_memory() -> str:
        """
        View all information stored in your permanent memory.
        Use this to see what the AI remembers about you.
        
        Returns:
            Summary of all stored memories (identity, preferences, facts)
        """
        memory = PersistentUserMemory(telegram_id)
        profile = memory.get_user_profile()
        
        if not profile:
            return "📭 No permanent memories stored yet.\n\nI will automatically remember:\n- Your name and company\n- Preferences you tell me\n- Things you ask me to remember"
        
        output = ["📋 **Your Permanent Memory**\n"]
        
        if memory.CATEGORY_IDENTITY in profile:
            output.append("**Identity:**")
            for key, value in profile[memory.CATEGORY_IDENTITY].items():
                output.append(f"  • {key.title()}: {value}")
            output.append("")
        
        if memory.CATEGORY_PREFERENCE in profile:
            output.append("**Preferences:**")
            for key, value in profile[memory.CATEGORY_PREFERENCE].items():
                output.append(f"  • {key}: {value}")
            output.append("")
        
        if memory.CATEGORY_FACT in profile:
            output.append("**Things to Remember:**")
            for key, value in profile[memory.CATEGORY_FACT].items():
                output.append(f"  • {value}")
            output.append("")
        
        if memory.CATEGORY_LEARNED in profile:
            output.append("**Learned from behavior:**")
            for key, value in profile[memory.CATEGORY_LEARNED].items():
                output.append(f"  • {value}")
        
        return "\n".join(output)
    
    @tool
    def forget_memory(what_to_forget: str) -> str:
        """
        Remove something from your permanent memory.
        
        Args:
            what_to_forget: What to forget - can be "name", "company", "email", 
                          "all preferences", "all facts", or "everything"
        
        Returns:
            Confirmation of what was forgotten
        """
        memory = PersistentUserMemory(telegram_id)
        what = what_to_forget.lower().strip()
        
        if what == "everything":
            memory.clear_all()
            return "🗑️ All permanent memories have been cleared."
        
        if what in ["name", "company", "email", "role"]:
            if memory.forget(memory.CATEGORY_IDENTITY, what):
                return f"🗑️ Forgot your {what}."
            return f"I don't have your {what} stored."
        
        if what == "all preferences":
            profile = memory.get_user_profile()
            if memory.CATEGORY_PREFERENCE in profile:
                for key in list(profile[memory.CATEGORY_PREFERENCE].keys()):
                    memory.forget(memory.CATEGORY_PREFERENCE, key)
                return "🗑️ All preferences cleared."
            return "No preferences stored."
        
        if what == "all facts":
            profile = memory.get_user_profile()
            if memory.CATEGORY_FACT in profile:
                for key in list(profile[memory.CATEGORY_FACT].keys()):
                    memory.forget(memory.CATEGORY_FACT, key)
                return "🗑️ All remembered facts cleared."
            return "No facts stored."
        
        # Try to match partial fact
        profile = memory.get_user_profile()
        if memory.CATEGORY_FACT in profile:
            for key, value in profile[memory.CATEGORY_FACT].items():
                if what in value.lower():
                    memory.forget(memory.CATEGORY_FACT, key)
                    return f"🗑️ Forgot: {value}"
        
        return f"Couldn't find '{what}' in memory. Use view_my_memory to see what's stored."
    
    @tool
    def remember_this(fact: str) -> str:
        """
        Explicitly store something in permanent memory.
        
        Args:
            fact: The fact or information to remember permanently
        
        Returns:
            Confirmation
        """
        memory = PersistentUserMemory(telegram_id)
        memory.remember_fact(fact)
        return f"💾 Remembered: {fact}"
    
    @tool
    def update_my_info(field: str, value: str) -> str:
        """
        Update your profile information.
        
        Args:
            field: The field to update - "name", "company", "email", "role"
            value: The new value
        
        Returns:
            Confirmation
        """
        memory = PersistentUserMemory(telegram_id)
        field = field.lower().strip()
        
        if field not in ["name", "company", "email", "role"]:
            return f"Unknown field: {field}. Use: name, company, email, or role"
        
        memory.set_value(memory.CATEGORY_IDENTITY, field, value)
        return f"✅ Updated your {field} to: {value}"
    
    return [view_my_memory, forget_memory, remember_this, update_my_info]
