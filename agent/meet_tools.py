"""
Google Meet + Places Tools - Smart meeting scheduling with location search.
Integrates Google Calendar (with Meet), Places API, and Gmail for invites.
"""

import os
from typing import Optional, List, Any
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool
from googleapiclient.discovery import build

from .google_auth import get_credentials


# Malaysia timezone
MYT = timezone(timedelta(hours=8))


def get_meet_tools(telegram_id: int) -> List[Any]:
    """Get meeting and places tools for a user."""
    tools = []
    
    credentials = get_credentials(telegram_id)
    if not credentials:
        return tools
    
    try:
        calendar_service = build('calendar', 'v3', credentials=credentials)
        gmail_service = build('gmail', 'v1', credentials=credentials)
    except Exception as e:
        print(f"[Meet Tools] Failed to create services: {e}")
        return tools
    
    @tool
    def schedule_meeting(
        title: str,
        date_time: str,
        attendee_email: Optional[str] = None,
        location: Optional[str] = None,
        duration_minutes: int = 60,
        description: str = "",
        add_google_meet: bool = True
    ) -> str:
        """
        Schedule a meeting with optional Google Meet link and location.
        
        Use this when the user wants to schedule a meeting, appointment, or call.
        Automatically creates a Google Calendar event with Meet link.
        
        Args:
            title: Meeting title (e.g. "Meeting with John", "Product Demo")
            date_time: When the meeting should be (e.g. "tomorrow 3pm", "2024-01-15 14:00")
            attendee_email: Optional email of the person to invite
            location: Optional physical location (can be searched via search_places)
            duration_minutes: Meeting length in minutes (default 60)
            description: Optional meeting description/agenda
            add_google_meet: Whether to add Google Meet video conferencing (default True)
        
        Returns:
            Meeting details with Meet link if added
        """
        try:
            # Parse the date_time
            meeting_time = parse_natural_datetime(date_time)
            if not meeting_time:
                return f"❌ Could not parse the date/time: '{date_time}'. Please use a clearer format like 'tomorrow 3pm' or '2024-01-15 14:00'"
            
            # Calculate end time
            end_time = meeting_time + timedelta(minutes=duration_minutes)
            
            # Build the event
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': meeting_time.isoformat(),
                    'timeZone': 'Asia/Kuala_Lumpur',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Kuala_Lumpur',
                },
            }
            
            # Add location if provided
            if location:
                event['location'] = location
            
            # Add attendee if provided
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
            
            # Add Google Meet conference
            if add_google_meet:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet_{datetime.now().timestamp()}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            
            # Create the event
            created_event = calendar_service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1 if add_google_meet else 0,
                sendUpdates='all' if attendee_email else 'none'
            ).execute()
            
            # Build response
            meet_link = ""
            if add_google_meet and created_event.get('conferenceData'):
                entry_points = created_event['conferenceData'].get('entryPoints', [])
                for ep in entry_points:
                    if ep.get('entryPointType') == 'video':
                        meet_link = ep.get('uri', '')
                        break
            
            output = f"✅ Meeting scheduled!\n\n"
            output += f"📅 {title}\n"
            output += f"🕐 {meeting_time.strftime('%A, %B %d at %I:%M %p')}\n"
            output += f"⏱️ Duration: {duration_minutes} minutes\n"
            
            if location:
                output += f"📍 Location: {location}\n"
            
            if meet_link:
                output += f"\n🔗 Google Meet: {meet_link}\n"
            
            if attendee_email:
                output += f"\n📧 Invite sent to: {attendee_email}\n"
            
            output += f"\n🔖 Event ID: {created_event.get('id')}"
            
            return output
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error scheduling meeting: {str(e)}"
    
    @tool
    def search_places(query: str, near: str = "Kuala Lumpur, Malaysia") -> str:
        """
        Search for places/locations using Google Places API.
        Limited to Malaysia for relevant results.
        
        Use this when the user mentions a place name and you need the full address.
        
        Args:
            query: What to search for (e.g. "Ativo Plaza", "Starbucks KLCC")
            near: Location to search near (default: Kuala Lumpur, Malaysia)
        
        Returns:
            List of matching places with addresses
        """
        try:
            import requests
            
            # Places API (New) requires API key, not OAuth
            api_key = os.getenv('GOOGLE_PLACES_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
            
            if not api_key:
                # Fallback: return the query as location directly
                return f"📍 '{query}' - Use this as the location when scheduling."
            
            # Use the Places API Text Search (New)
            url = "https://places.googleapis.com/v1/places:searchText"
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating"
            }
            
            request_body = {
                "textQuery": f"{query} {near}",
                "maxResultCount": 5,
                "locationRestriction": {
                    "rectangle": {
                        # Malaysia bounding box (approximate)
                        "low": {"latitude": 0.8, "longitude": 99.0},
                        "high": {"latitude": 7.5, "longitude": 119.5}
                    }
                }
            }
            
            response = requests.post(url, json=request_body, headers=headers)
            
            if response.status_code != 200:
                print(f"[Places] Error {response.status_code}: {response.text}")
                return f"📍 '{query}' - Use this as the location when scheduling."
            
            data = response.json()
            places = data.get('places', [])
            
            if not places:
                return f"❌ No places found matching '{query}' in Malaysia."
            
            output = f"📍 Found {len(places)} place(s) for '{query}':\n\n"
            
            for i, place in enumerate(places, 1):
                name = place.get('displayName', {}).get('text', 'Unknown')
                address = place.get('formattedAddress', 'No address')
                rating = place.get('rating', '')
                
                output += f"{i}. {name}\n"
                output += f"   📍 {address}\n"
                if rating:
                    output += f"   ⭐ Rating: {rating}\n"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            # Fallback: Just return the query as the location
            print(f"[Places] Error: {e}")
            return f"📍 Could not search Places API. You can use '{query}' as the location directly when scheduling."
    
    @tool
    def send_meeting_invite(
        event_id: str,
        email: str,
        personal_message: str = ""
    ) -> str:
        """
        Send a meeting invite email to someone for an existing calendar event.
        
        Args:
            event_id: The calendar event ID (from schedule_meeting result)
            email: Email address to send the invite to
            personal_message: Optional personal message to include
        
        Returns:
            Success or error message
        """
        try:
            # Get the event details
            event = calendar_service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Add the attendee
            attendees = event.get('attendees', [])
            if not any(a.get('email') == email for a in attendees):
                attendees.append({'email': email})
                event['attendees'] = attendees
                
                # Update the event
                calendar_service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event,
                    sendUpdates='all'
                ).execute()
            
            # Get Meet link if available
            meet_link = ""
            if event.get('conferenceData'):
                entry_points = event['conferenceData'].get('entryPoints', [])
                for ep in entry_points:
                    if ep.get('entryPointType') == 'video':
                        meet_link = ep.get('uri', '')
                        break
            
            # Send a personal email with details
            if personal_message:
                import base64
                from email.mime.text import MIMEText
                
                summary = event.get('summary', 'Meeting')
                start = event.get('start', {}).get('dateTime', '')
                location = event.get('location', '')
                
                email_body = f"""Hi,

{personal_message}

Meeting Details:
- {summary}
- Time: {start}
{"- Location: " + location if location else ""}
{"- Join: " + meet_link if meet_link else ""}

Looking forward to our meeting!
"""
                
                message = MIMEText(email_body)
                message['to'] = email
                message['subject'] = f"Meeting Invite: {summary}"
                
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                gmail_service.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute()
            
            return f"✅ Invite sent to {email}!"
            
        except Exception as e:
            return f"❌ Error sending invite: {str(e)}"
    
    tools.extend([schedule_meeting, search_places, send_meeting_invite])
    print(f"[Meet Tools] Loaded 3 meeting tools")
    
    return tools


def parse_natural_datetime(text: str) -> Optional[datetime]:
    """
    Parse natural language date/time expressions.
    Returns datetime in Malaysia timezone.
    """
    now = datetime.now(MYT)
    text = text.lower().strip()
    
    # Handle relative dates
    if 'tomorrow' in text:
        target_date = now + timedelta(days=1)
    elif 'today' in text:
        target_date = now
    elif 'next week' in text:
        target_date = now + timedelta(weeks=1)
    elif 'monday' in text:
        target_date = next_weekday(now, 0)
    elif 'tuesday' in text:
        target_date = next_weekday(now, 1)
    elif 'wednesday' in text:
        target_date = next_weekday(now, 2)
    elif 'thursday' in text:
        target_date = next_weekday(now, 3)
    elif 'friday' in text:
        target_date = next_weekday(now, 4)
    elif 'saturday' in text:
        target_date = next_weekday(now, 5)
    elif 'sunday' in text:
        target_date = next_weekday(now, 6)
    else:
        target_date = now
    
    # Extract time
    import re
    
    # Try various time patterns
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 3:00, 3:00pm
        r'(\d{1,2})\s*(am|pm)',            # 3pm, 3 pm
        r'at\s+(\d{1,2})(?::(\d{2}))?',    # at 3, at 3:00
    ]
    
    hour, minute = 10, 0  # Default to 10am if no time specified
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            hour = int(groups[0])
            
            if len(groups) > 1 and groups[1] and groups[1].isdigit():
                minute = int(groups[1])
            elif len(groups) > 1 and groups[1] in ['am', 'pm']:
                if groups[1] == 'pm' and hour < 12:
                    hour += 12
            elif len(groups) > 2 and groups[2] in ['am', 'pm']:
                if groups[2] == 'pm' and hour < 12:
                    hour += 12
            break
    
    # Also try to parse ISO format
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=MYT)
    except:
        pass
    
    # Try parsing with dateutil if available
    try:
        from dateutil import parser as dateutil_parser
        parsed = dateutil_parser.parse(text, fuzzy=True)
        return parsed.replace(tzinfo=MYT)
    except:
        pass
    
    # Build the final datetime
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def next_weekday(d: datetime, weekday: int) -> datetime:
    """Get the next occurrence of a weekday (0=Monday, 6=Sunday)."""
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)
