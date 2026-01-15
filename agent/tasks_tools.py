"""
Google Tasks Tools - Note-taking via Google Tasks API.
Provides CRUD operations for notes/tasks with date filtering support.
"""

import os
from typing import Optional, List, Any
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool
from googleapiclient.discovery import build

from .google_auth import get_credentials


# Malaysia timezone
MYT = timezone(timedelta(hours=8))

# Default task list name for notes
NOTES_LIST_NAME = "Telegram Notes"


def get_tasks_tools(telegram_id: int) -> List[Any]:
    """Get Google Tasks tools for note-taking."""
    tools = []
    
    credentials = get_credentials(telegram_id)
    if not credentials:
        return tools
    
    try:
        service = build('tasks', 'v1', credentials=credentials)
    except Exception as e:
        print(f"[Tasks Tools] Failed to create service: {e}")
        return tools
    
    def get_or_create_notes_list():
        """Get or create the notes task list."""
        try:
            # List all task lists
            results = service.tasklists().list().execute()
            lists = results.get('items', [])
            
            # Find existing notes list
            for lst in lists:
                if lst.get('title') == NOTES_LIST_NAME:
                    return lst.get('id')
            
            # Create new list
            new_list = service.tasklists().insert(body={'title': NOTES_LIST_NAME}).execute()
            print(f"[Tasks] Created new task list: {NOTES_LIST_NAME}")
            return new_list.get('id')
            
        except Exception as e:
            print(f"[Tasks] Error getting/creating list: {e}")
            return None
    
    @tool
    def create_note(content: str, title: str = "") -> str:
        """
        Save a note to Google Tasks.
        Use this when the user says "note this", "remember this", "save this note", etc.
        
        Args:
            content: The note content to save
            title: Optional title for the note (auto-generated if not provided)
        
        Returns:
            Confirmation message
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks. Please try again."
            
            # Auto-generate title if not provided
            if not title:
                # Use first line or first few words
                first_line = content.split('\n')[0][:50]
                title = first_line + ("..." if len(content) > 50 else "")
            
            # Create the task (note)
            now = datetime.now(MYT)
            task_body = {
                'title': title,
                'notes': content,
                'status': 'needsAction'  # Keeps it visible
            }
            
            result = service.tasks().insert(
                tasklist=list_id,
                body=task_body
            ).execute()
            
            return f"✅ Note saved!\n\n📝 \"{title}\"\n📅 {now.strftime('%B %d, %Y at %I:%M %p')}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error saving note: {str(e)}"
    
    @tool
    def list_notes(limit: int = 10, include_completed: bool = False) -> str:
        """
        List all saved notes from Google Tasks.
        Use this when the user asks "what are my notes", "show my notes", etc.
        
        Args:
            limit: Maximum number of notes to return (default 10)
            include_completed: Whether to include completed/archived notes
        
        Returns:
            List of notes with titles and dates
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks."
            
            # Get tasks
            results = service.tasks().list(
                tasklist=list_id,
                maxResults=limit,
                showCompleted=include_completed,
                showHidden=include_completed
            ).execute()
            
            tasks = results.get('items', [])
            
            if not tasks:
                return "📝 You don't have any notes yet.\n\nSay 'Note: [your content]' to save a note."
            
            output = f"📝 Your Notes ({len(tasks)} found):\n\n"
            
            for i, task in enumerate(tasks, 1):
                title = task.get('title', 'Untitled')
                notes = task.get('notes', '')
                updated = task.get('updated', '')
                
                # Parse date
                date_str = ""
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        date_str = dt.strftime('%b %d, %Y')
                    except:
                        pass
                
                output += f"{i}. {title}\n"
                if notes:
                    preview = notes[:80] + ("..." if len(notes) > 80 else "")
                    output += f"   {preview}\n"
                if date_str:
                    output += f"   📅 {date_str}\n"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error listing notes: {str(e)}"
    
    @tool
    def search_notes(query: str) -> str:
        """
        Search through notes by content or title.
        Use this when the user asks "find my note about X", "what did I note about X", etc.
        
        Args:
            query: Search term to look for in note titles and content
        
        Returns:
            Matching notes
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks."
            
            # Get all tasks and search locally (Tasks API doesn't have search)
            results = service.tasks().list(
                tasklist=list_id,
                maxResults=100,
                showCompleted=True,
                showHidden=True
            ).execute()
            
            tasks = results.get('items', [])
            query_lower = query.lower()
            
            matches = []
            for task in tasks:
                title = task.get('title', '').lower()
                notes = task.get('notes', '').lower()
                
                if query_lower in title or query_lower in notes:
                    matches.append(task)
            
            if not matches:
                return f"❌ No notes found containing '{query}'."
            
            output = f"🔍 Found {len(matches)} note(s) matching '{query}':\n\n"
            
            for i, task in enumerate(matches[:10], 1):
                title = task.get('title', 'Untitled')
                notes = task.get('notes', '')
                
                output += f"{i}. {title}\n"
                if notes:
                    output += f"   {notes[:150]}{'...' if len(notes) > 150 else ''}\n"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error searching notes: {str(e)}"
    
    @tool
    def get_notes_by_date(date_str: str) -> str:
        """
        Get notes from a specific date.
        Use this when the user asks about notes from a particular day.
        
        Args:
            date_str: Date to search for (e.g., "yesterday", "January 15", "2024-01-15")
        
        Returns:
            Notes from that date
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks."
            
            # Parse the date
            target_date = parse_date(date_str)
            if not target_date:
                return f"❌ Could not understand the date '{date_str}'. Try formats like 'yesterday', 'January 15', or '2024-01-15'."
            
            # Get all tasks
            results = service.tasks().list(
                tasklist=list_id,
                maxResults=100,
                showCompleted=True,
                showHidden=True
            ).execute()
            
            tasks = results.get('items', [])
            
            # Filter by date
            matches = []
            for task in tasks:
                updated = task.get('updated', '')
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        if dt.date() == target_date.date():
                            matches.append(task)
                    except:
                        pass
            
            if not matches:
                return f"📝 No notes found from {target_date.strftime('%B %d, %Y')}."
            
            output = f"📝 Notes from {target_date.strftime('%B %d, %Y')} ({len(matches)} found):\n\n"
            
            for i, task in enumerate(matches, 1):
                title = task.get('title', 'Untitled')
                notes = task.get('notes', '')
                
                output += f"{i}. {title}\n"
                if notes:
                    output += f"   {notes[:150]}{'...' if len(notes) > 150 else ''}\n"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error getting notes: {str(e)}"
    
    @tool
    def delete_note(note_title: str) -> str:
        """
        Delete a note by its title.
        Use this when the user wants to remove a specific note.
        
        Args:
            note_title: Title or partial title of the note to delete
        
        Returns:
            Confirmation or error message
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks."
            
            # Find the note
            results = service.tasks().list(
                tasklist=list_id,
                maxResults=100
            ).execute()
            
            tasks = results.get('items', [])
            title_lower = note_title.lower()
            
            found = None
            for task in tasks:
                if title_lower in task.get('title', '').lower():
                    found = task
                    break
            
            if not found:
                return f"❌ No note found matching '{note_title}'."
            
            # Delete the task
            service.tasks().delete(
                tasklist=list_id,
                task=found.get('id')
            ).execute()
            
            return f"✅ Note deleted: \"{found.get('title')}\""
            
        except Exception as e:
            return f"❌ Error deleting note: {str(e)}"
    
    @tool
    def update_note(note_title: str, new_content: str, new_title: str = "") -> str:
        """
        Update an existing note's content or title.
        Use this when the user wants to modify a saved note.
        
        Args:
            note_title: Title or partial title of the note to update
            new_content: New content for the note
            new_title: Optional new title (keeps original if not provided)
        
        Returns:
            Confirmation or error message
        """
        try:
            list_id = get_or_create_notes_list()
            if not list_id:
                return "❌ Could not access Google Tasks."
            
            # Find the note
            results = service.tasks().list(
                tasklist=list_id,
                maxResults=100
            ).execute()
            
            tasks = results.get('items', [])
            title_lower = note_title.lower()
            
            found = None
            for task in tasks:
                if title_lower in task.get('title', '').lower():
                    found = task
                    break
            
            if not found:
                return f"❌ No note found matching '{note_title}'."
            
            # Update the task
            update_body = {
                'id': found.get('id'),
                'title': new_title if new_title else found.get('title'),
                'notes': new_content
            }
            
            service.tasks().update(
                tasklist=list_id,
                task=found.get('id'),
                body=update_body
            ).execute()
            
            return f"✅ Note updated: \"{update_body['title']}\""
            
        except Exception as e:
            return f"❌ Error updating note: {str(e)}"
    
    tools.extend([create_note, list_notes, search_notes, get_notes_by_date, delete_note, update_note])
    print(f"[Tasks Tools] Loaded 6 note-taking tools")
    
    return tools


def parse_date(text: str) -> Optional[datetime]:
    """Parse natural language date expressions."""
    now = datetime.now(MYT)
    text = text.lower().strip()
    
    # Handle relative dates
    if text == 'today':
        return now
    elif text == 'yesterday':
        return now - timedelta(days=1)
    elif text == 'last week':
        return now - timedelta(weeks=1)
    
    # Try ISO format
    try:
        return datetime.fromisoformat(text).replace(tzinfo=MYT)
    except:
        pass
    
    # Try with dateutil
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(text, fuzzy=True).replace(tzinfo=MYT)
    except:
        pass
    
    return None
