"""
Google People API Tools for Contact Management.
Provides tools to save and search contacts via Google People API.
"""

from typing import Optional, List, Dict
from langchain_core.tools import tool
from .google_auth import get_credentials


def get_people_tools(telegram_id: int) -> list:
    """
    Create Google People API tools for a specific user.
    Returns a list of LangChain tools bound to the user's credentials.
    """
    
    credentials = get_credentials(telegram_id)
    if not credentials:
        return []
    
    try:
        from googleapiclient.discovery import build
        service = build('people', 'v1', credentials=credentials)
    except Exception as e:
        print(f"[People] Error building service: {e}")
        return []
    
    @tool
    def save_contact(
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        job_title: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Save a new contact to Google Contacts.
        Use this when user wants to save contact information from a namecard or text.
        
        Args:
            name: Full name of the contact (required)
            phone: Phone number
            email: Email address
            company: Company/organization name
            job_title: Job title or position
            notes: Additional notes about the contact
        
        Returns:
            Success message with contact details, or error message
        """
        try:
            # Build contact body
            contact_body = {
                "names": [{"givenName": name}],
            }
            
            # Parse name into given/family if possible
            name_parts = name.strip().split()
            if len(name_parts) >= 2:
                contact_body["names"] = [{
                    "givenName": " ".join(name_parts[:-1]),
                    "familyName": name_parts[-1]
                }]
            
            # Add optional fields
            if phone:
                contact_body["phoneNumbers"] = [{"value": phone, "type": "mobile"}]
            
            if email:
                contact_body["emailAddresses"] = [{"value": email, "type": "work"}]
            
            if company:
                org = {"name": company}
                if job_title:
                    org["title"] = job_title
                contact_body["organizations"] = [org]
            elif job_title:
                contact_body["organizations"] = [{"title": job_title}]
            
            if notes:
                contact_body["biographies"] = [{"value": notes, "contentType": "TEXT_PLAIN"}]
            
            # Create the contact
            result = service.people().createContact(body=contact_body).execute()
            
            resource_name = result.get('resourceName', '')
            
            # Build confirmation message
            details = [f"Name: {name}"]
            if phone:
                details.append(f"Phone: {phone}")
            if email:
                details.append(f"Email: {email}")
            if company:
                details.append(f"Company: {company}")
            if job_title:
                details.append(f"Title: {job_title}")
            
            return f"✅ Contact saved successfully!\n" + "\n".join(details)
            
        except Exception as e:
            return f"❌ Error saving contact: {str(e)}"
    
    @tool
    def find_contact(search_query: str) -> str:
        """
        Search for a contact by name, email, or company.
        Use this when user asks to find or look up a contact.
        
        Args:
            search_query: Name, email, or company to search for
        
        Returns:
            Contact details if found, or message if not found
        """
        try:
            # Search in user's contacts
            results = service.people().searchContacts(
                query=search_query,
                readMask="names,emailAddresses,phoneNumbers,organizations"
            ).execute()
            
            contacts = results.get('results', [])
            
            if not contacts:
                return f"❌ No contacts found matching '{search_query}'"
            
            # Format results
            output = f"📇 Found {len(contacts)} contact(s):\n\n"
            
            for i, contact in enumerate(contacts[:5], 1):  # Limit to 5 results
                person = contact.get('person', {})
                
                # Get name
                names = person.get('names', [])
                name = names[0].get('displayName', 'Unknown') if names else 'Unknown'
                
                # Get email
                emails = person.get('emailAddresses', [])
                email = emails[0].get('value', '') if emails else ''
                
                # Get phone
                phones = person.get('phoneNumbers', [])
                phone = phones[0].get('value', '') if phones else ''
                
                # Get company
                orgs = person.get('organizations', [])
                company = orgs[0].get('name', '') if orgs else ''
                title = orgs[0].get('title', '') if orgs else ''
                
                output += f"{i}. {name}\n"
                if email:
                    output += f"   Email: {email}\n"
                if phone:
                    output += f"   Phone: {phone}\n"
                if company:
                    output += f"   Company: {company}\n"
                if title:
                    output += f"   Title: {title}\n"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error searching contacts: {str(e)}"
    
    @tool
    def list_contacts(limit: int = 10) -> str:
        """
        List recent contacts from Google Contacts.
        
        Args:
            limit: Maximum number of contacts to return (default: 10)
        
        Returns:
            List of contacts with their details
        """
        try:
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=min(limit, 50),
                personFields='names,emailAddresses,phoneNumbers,organizations'
            ).execute()
            
            connections = results.get('connections', [])
            
            if not connections:
                return "📇 No contacts found in your Google Contacts."
            
            output = f"📇 Your contacts ({len(connections)}):\n\n"
            
            for i, person in enumerate(connections, 1):
                # Get name
                names = person.get('names', [])
                name = names[0].get('displayName', 'Unknown') if names else 'Unknown'
                
                # Get email
                emails = person.get('emailAddresses', [])
                email = emails[0].get('value', '') if emails else ''
                
                # Get company
                orgs = person.get('organizations', [])
                company = orgs[0].get('name', '') if orgs else ''
                
                output += f"{i}. {name}"
                if email:
                    output += f" - {email}"
                if company:
                    output += f" ({company})"
                output += "\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error listing contacts: {str(e)}"
    
    return [save_contact, find_contact, list_contacts]
