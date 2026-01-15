"""
Google Tools - Custom LangChain tools for Google Drive, Sheets, Gmail, Calendar.
Uses official Google APIs with LangChain Tool wrapper for function calling.
"""
from typing import List, Any, Optional
from langchain_core.tools import tool
from googleapiclient.discovery import build


def get_google_tools(telegram_id: int) -> List[Any]:
    """
    Get LangChain Google tools for a specific user.
    Creates custom tools that use Google APIs directly.
    """
    tools = []
    
    # ALWAYS add universal tools (available even without Google connection)
    tools.append(create_connection_check_tool(telegram_id))
    tools.append(create_web_fetch_tool())
    
    # Add chart tools (no credentials needed)
    from .chart_tools import get_chart_tools
    tools.extend(get_chart_tools())
    
    try:
        from .google_auth import get_credentials
        from .people_tools import get_people_tools
        from .catalogue_tools import get_catalogue_tools
        from .quotation_tools import get_quotation_tools
        from .memory_tools import get_memory_tools
        from .meet_tools import get_meet_tools
        from .tasks_tools import get_tasks_tools
        
        # Add memory tools (always available, no credentials needed)
        tools.extend(get_memory_tools(telegram_id))
        
        credentials = get_credentials(telegram_id)
        if not credentials:
            print(f"[Google Tools] No credentials for user {telegram_id}")
            return tools  # Return with just the connection check tool + memory tools
        
        print(f"[Google Tools] Loading tools for user {telegram_id}")
        
        # Create tools with the user's credentials
        tools.extend(create_gmail_tools(credentials))
        tools.extend(create_drive_tools(credentials))
        tools.extend(create_sheets_tools(credentials))
        tools.extend(create_calendar_tools(credentials))
        tools.extend(get_people_tools(telegram_id))  # Add People API tools
        tools.extend(get_catalogue_tools(telegram_id))  # Add Catalogue tools
        tools.extend(get_quotation_tools(telegram_id))  # Add Quotation tools
        tools.extend(get_meet_tools(telegram_id))  # Add Meet + Places tools
        tools.extend(get_tasks_tools(telegram_id))  # Add Tasks (notes) tools
        
        print(f"[Google Tools] Total tools loaded: {len(tools)}")
        
    except Exception as e:
        print(f"[Google Tools] Error loading tools for user {telegram_id}: {e}")
        import traceback
        traceback.print_exc()
    
    return tools


def create_connection_check_tool(telegram_id: int) -> Any:
    """Create a tool that checks if user has Google services connected."""
    from .google_auth import has_google_credentials
    
    @tool
    def check_google_connection_status() -> str:
        """
        SILENTLY check if the user has connected their Google account.
        Use this BEFORE any Google operation (Gmail, Drive, Sheets, Calendar).
        
        CRITICAL INSTRUCTIONS:
        - DO NOT tell the user you are checking. Just check silently.
        - If connected: Proceed immediately with the requested operation (search emails, list files, etc).
        - If NOT connected: Tell them ONCE to use /register_google and explain they need to connect first.
        - Never say "I am checking" or "please wait" - just check and act.
        """
        is_connected = has_google_credentials(telegram_id)
        
        if is_connected:
            return "CONNECTED: User has Google account linked. Proceed with the requested operation immediately."
        else:
            return "NOT_CONNECTED: User has NOT linked Google account. You must inform them to use /register_google command to connect their account before proceeding."
    
    return check_google_connection_status


def create_web_fetch_tool() -> Any:
    """Create a tool that fetches content from URLs using Jina Reader API."""
    
    @tool
    def fetch_url_content(url: str) -> str:
        """
        Fetch and extract the main text content from any webpage URL.
        This tool can handle JavaScript-rendered pages, social media posts, and complex websites.
        Use this when the user provides a link and wants you to read/analyze its content.
        
        Args:
            url: The full URL to fetch (e.g. 'https://example.com/article' or 'https://facebook.com/post/...')
        
        Returns:
            The extracted text content from the page in readable format
        """
        try:
            import requests
            
            # Use Jina Reader API - free, handles JavaScript, no API key needed
            # Simply prepend https://r.jina.ai/ to any URL
            jina_url = f"https://r.jina.ai/{url}"
            
            headers = {
                'Accept': 'text/plain',
                'User-Agent': 'Mozilla/5.0 (compatible; TelegramBot/1.0)'
            }
            
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text.strip()
            
            # Limit content length for token efficiency
            if len(content) > 6000:
                content = content[:6000] + "\n\n... [content truncated due to length]"
            
            if not content:
                return f"Could not extract readable content from {url}"
            
            return f"Content from {url}:\n\n{content}"
            
        except requests.Timeout:
            return f"Error: Request to {url} timed out (page may be too slow)"
        except requests.RequestException as e:
            return f"Error fetching {url}: {str(e)}"
        except Exception as e:
            return f"Error processing {url}: {str(e)}"
    
    return fetch_url_content


def create_gmail_tools(credentials) -> List[Any]:
    """Create Gmail tools with user's credentials."""
    tools = []
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        @tool
        def get_my_email_info() -> str:
            """
            Get the current user's Gmail email address and profile info.
            Use this when you need to know the user's email address or identity.
            """
            try:
                profile = service.users().getProfile(userId='me').execute()
                email = profile.get('emailAddress', 'Unknown')
                total_messages = profile.get('messagesTotal', 0)
                return f"User's email: {email}\nTotal messages in inbox: {total_messages}"
            except Exception as e:
                return f"Error getting profile: {str(e)}"
        
        @tool
        def search_gmail(query: str) -> str:
            """Search Gmail inbox. Use queries like 'from:example@gmail.com' or 'subject:meeting'."""
            try:
                results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
                messages = results.get('messages', [])
                if not messages:
                    return "No messages found matching your query."
                
                output = []
                for msg in messages[:5]:
                    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                    output.append(f"From: {headers.get('From', 'Unknown')}\nSubject: {headers.get('Subject', 'No Subject')}\nDate: {headers.get('Date', 'Unknown')}\n")
                return "\n---\n".join(output)
            except Exception as e:
                return f"Error searching Gmail: {str(e)}"
        
        @tool
        def read_gmail_message(message_id: str) -> str:
            """Read a specific Gmail message by its ID."""
            try:
                msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                snippet = msg.get('snippet', 'No content')
                return f"From: {headers.get('From')}\nSubject: {headers.get('Subject')}\nContent: {snippet}"
            except Exception as e:
                return f"Error reading message: {str(e)}"
        
        @tool
        def send_email(to: str, subject: str, body: str) -> str:
            """
            Send an email via Gmail.
            
            Args:
                to: Email address of the recipient (e.g. 'example@gmail.com')
                subject: Subject line of the email
                body: Plain text body content of the email
            
            Returns:
                Success or error message
            """
            try:
                import base64
                from email.mime.text import MIMEText
                
                # Create the email message
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject
                
                # Encode the message
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                
                # Send it
                sent_message = service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                return f"✅ Email sent successfully to {to}! Message ID: {sent_message['id']}"
            except Exception as e:
                return f"❌ Error sending email: {str(e)}"
        
        tools.extend([get_my_email_info, search_gmail, read_gmail_message, send_email])
        print(f"[Google Tools] Loaded 4 Gmail tools")
        
    except Exception as e:
        print(f"[Google Tools] Failed to create Gmail tools: {e}")
    
    return tools


def create_drive_tools(credentials) -> List[Any]:
    """Create Google Drive tools with user's credentials."""
    tools = []
    
    try:
        service = build('drive', 'v3', credentials=credentials)
        
        @tool
        def list_drive_files(query: str = "") -> str:
            """List files in Google Drive. Optional query to filter (e.g., 'name contains insurance')."""
            try:
                q = query if query else None
                results = service.files().list(
                    pageSize=20, 
                    fields="files(id, name, mimeType, modifiedTime)",
                    q=q if q else None
                ).execute()
                files = results.get('files', [])
                if not files:
                    return "No files found in Drive."
                
                output = []
                for f in files:
                    output.append(f"📄 {f['name']} (ID: {f['id']}, Modified: {f.get('modifiedTime', 'Unknown')})")
                return "\n".join(output)
            except Exception as e:
                return f"Error listing Drive files: {str(e)}"
        
        @tool
        def search_drive_files(search_term: str) -> str:
            """Search for files in Google Drive by name."""
            try:
                query = f"name contains '{search_term}'"
                results = service.files().list(
                    pageSize=20,
                    fields="files(id, name, mimeType, modifiedTime)",
                    q=query
                ).execute()
                files = results.get('files', [])
                if not files:
                    return f"No files found matching '{search_term}'."
                
                output = []
                for f in files:
                    output.append(f"📄 {f['name']} (ID: {f['id']})")
                return "\n".join(output)
            except Exception as e:
                return f"Error searching Drive: {str(e)}"
        
        @tool
        def get_drive_file_content(file_id: str) -> str:
            """Get the content of a Google Drive file by its ID. Works for Google Docs and text files."""
            try:
                # Get file metadata first
                file_meta = service.files().get(fileId=file_id, fields="mimeType,name").execute()
                mime_type = file_meta.get('mimeType', '')
                
                if 'spreadsheet' in mime_type:
                    return f"This is a Google Sheet. Use the sheets tools to read its content."
                elif 'document' in mime_type:
                    # Export Google Doc as plain text
                    content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
                    return content.decode('utf-8')[:2000]  # Limit content
                else:
                    return f"File: {file_meta.get('name')} (Type: {mime_type}). Cannot read binary files directly."
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        @tool
        def read_pdf_from_drive(file_identifier: str) -> str:
            """
            Download and analyze a PDF file from Google Drive.
            Use this when user asks to read/analyze a PDF file in their Drive.
            
            Args:
                file_identifier: Name or URL of the PDF file in Drive
            
            Returns:
                Text content extracted from the PDF or analysis results
            """
            try:
                from google import genai
                import fitz  # PyMuPDF
                import io
                from googleapiclient.http import MediaIoBaseDownload
                import os
                
                # Search for the file
                file_id = None
                file_name = "PDF file"
                
                if "drive.google.com" in file_identifier:
                    # Extract file ID from URL
                    import re
                    match = re.search(r'/d/([a-zA-Z0-9_-]+)', file_identifier)
                    if match:
                        file_id = match.group(1)
                    else:
                        return "❌ Invalid Google Drive URL"
                elif len(file_identifier) > 20 and not " " in file_identifier and file_identifier.replace("-", "").replace("_", "").isalnum():
                    # Looks like a file ID (long alphanumeric string with no spaces)
                    file_id = file_identifier
                    # Try to get the file name
                    try:
                        file_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
                        file_name = file_meta.get('name', 'PDF file')
                        if file_meta.get('mimeType') != 'application/pdf':
                            return f"❌ File '{file_name}' is not a PDF (it's {file_meta.get('mimeType')})"
                    except Exception as e:
                        return f"❌ Could not find file with ID '{file_identifier}': {str(e)}"
                else:
                    # Search by name
                    query = f"name contains '{file_identifier}' and mimeType = 'application/pdf' and trashed = false"
                    results = service.files().list(
                        q=query,
                        pageSize=5,
                        fields="files(id, name)"
                    ).execute()
                    
                    files = results.get('files', [])
                    if not files:
                        return f"❌ No PDF found matching '{file_identifier}'"
                    
                    if len(files) > 1:
                        file_list = "\n".join([f"  • {f['name']} (ID: {f['id']})" for f in files])
                        return f"Found multiple PDFs:\n{file_list}\n\nPlease use the specific file ID."
                    
                    file_id = files[0]['id']
                    file_name = files[0]['name']
                
                # Download the PDF
                request = service.files().get_media(fileId=file_id)
                pdf_data = io.BytesIO()
                downloader = MediaIoBaseDownload(pdf_data, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                pdf_bytes = pdf_data.getvalue()
                
                # Use Gemini Vision to analyze the PDF
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    return "❌ GEMINI_API_KEY not configured"
                
                client = genai.Client(api_key=api_key)
                
                # Convert PDF to images and analyze
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                analysis_results = []
                
                for page_num in range(min(len(doc), 10)):  # Limit to 10 pages
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[
                            {"inline_data": {"mime_type": "image/png", "data": img_bytes}},
                            "Analyze this page and extract all text and information you can find. Be detailed and comprehensive."
                        ]
                    )
                    
                    analysis_results.append(f"📄 Page {page_num + 1}:\n{response.text}")
                
                doc.close()
                
                return f"📁 Analysis of '{file_name}':\n\n" + "\n\n".join(analysis_results)
                
            except ImportError:
                return "❌ PDF processing libraries not installed. Contact admin."
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"❌ Error reading PDF: {str(e)}"
        
        
        @tool
        def create_drive_folder(folder_name: str, parent_folder_name: str = "") -> str:
            """
            Create a new folder in Google Drive.
            Use this when user wants to create a folder to organize files.
            
            Args:
                folder_name: Name of the folder to create
                parent_folder_name: Optional name of parent folder (creates in root if not specified)
            
            Returns:
                Folder ID and success message
            """
            try:
                parent_id = None
                
                # Find parent folder if specified
                if parent_folder_name:
                    query = f"name = '{parent_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    results = service.files().list(q=query, fields="files(id, name)").execute()
                    files = results.get('files', [])
                    if files:
                        parent_id = files[0]['id']
                
                # Check if folder already exists
                check_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                if parent_id:
                    check_query += f" and '{parent_id}' in parents"
                
                existing = service.files().list(q=check_query, fields="files(id, name)").execute()
                if existing.get('files'):
                    folder_id = existing['files'][0]['id']
                    return f"📁 Folder '{folder_name}' already exists. ID: {folder_id}"
                
                # Create the folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                folder = service.files().create(body=file_metadata, fields='id').execute()
                folder_id = folder.get('id')
                
                return f"✅ Created folder '{folder_name}'. ID: {folder_id}"
                
            except Exception as e:
                return f"❌ Error creating folder: {str(e)}"
        
        @tool
        def upload_file_to_folder(folder_name: str, file_name: str = "") -> str:
            """
            Upload the file that was sent in the current message to a specific folder in Drive.
            Use this when user sends a file and wants it saved to a specific folder.
            Creates the folder if it doesn't exist.
            
            Args:
                folder_name: Name of the folder to save the file in (will be created if doesn't exist)
                file_name: Optional custom name for the file (uses original name if not specified)
            
            Returns:
                Success message with file link
            """
            try:
                from bot.config import telegram_agent
                from googleapiclient.http import MediaIoBaseUpload
                import io
                
                # Get file context
                # We need to figure out the telegram_id - this is captured in closure
                # But upload_file_to_folder is a generic tool, need a different approach
                # For now, return instruction
                
                # First, find or create the folder
                query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                results = service.files().list(q=query, fields="files(id, name)").execute()
                folders = results.get('files', [])
                
                if folders:
                    folder_id = folders[0]['id']
                else:
                    # Create the folder
                    folder_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = service.files().create(body=folder_metadata, fields='id').execute()
                    folder_id = folder.get('id')
                
                return f"✅ Folder '{folder_name}' is ready. ID: {folder_id}\n\nTo save the uploaded file there, use the save_catalogue tool with folder support or I'll move the file for you."
                
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        @tool
        def copy_file(
            file_url_or_id: str,
            new_name: str = "",
            destination_folder: str = ""
        ) -> str:
            """
            Copy a file or spreadsheet from a shared link to the user's Drive.
            This preserves ALL formatting (colors, fonts, styles, formulas).
            
            Use this when:
            - User shares a Google Sheets/Docs/file link from another account
            - User wants to copy a shared file to their own Drive
            - User wants to duplicate a file
            
            Args:
                file_url_or_id: The shared link URL (e.g., https://docs.google.com/spreadsheets/d/xxx) or file ID
                new_name: Optional new name for the copy (uses original if not specified)
                destination_folder: Optional folder name to put the copy in (uses root if not specified)
            
            Returns:
                Success message with new file link or error
            """
            import re
            
            try:
                # Extract file ID from URL if needed
                file_id = file_url_or_id
                
                # Try to extract ID from various Google URL formats
                url_patterns = [
                    r'/d/([a-zA-Z0-9_-]+)',  # /d/FILE_ID format
                    r'id=([a-zA-Z0-9_-]+)',  # id=FILE_ID format
                    r'^([a-zA-Z0-9_-]{25,})$'  # Just the ID
                ]
                
                for pattern in url_patterns:
                    match = re.search(pattern, file_url_or_id)
                    if match:
                        file_id = match.group(1)
                        break
                
                # Get original file info
                try:
                    original = service.files().get(fileId=file_id, fields='name,mimeType').execute()
                    original_name = original.get('name', 'Copied File')
                    mime_type = original.get('mimeType', '')
                except Exception as e:
                    return f"❌ Could not access the file. Make sure it's shared with 'Anyone with the link' or with your Google account. Error: {str(e)}"
                
                # Determine destination folder
                folder_id = None
                if destination_folder:
                    # Search for folder
                    query = f"name = '{destination_folder}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    results = service.files().list(q=query, fields="files(id)").execute()
                    folders = results.get('files', [])
                    
                    if folders:
                        folder_id = folders[0]['id']
                    else:
                        # Create the folder
                        folder_metadata = {
                            'name': destination_folder,
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                        folder = service.files().create(body=folder_metadata, fields='id').execute()
                        folder_id = folder.get('id')
                
                # Prepare copy metadata
                copy_name = new_name if new_name else f"Copy of {original_name}"
                copy_metadata = {'name': copy_name}
                
                if folder_id:
                    copy_metadata['parents'] = [folder_id]
                
                # Make the copy
                copied = service.files().copy(
                    fileId=file_id,
                    body=copy_metadata,
                    fields='id,name,webViewLink'
                ).execute()
                
                copied_id = copied.get('id')
                copied_name = copied.get('name')
                copied_link = copied.get('webViewLink', f"https://drive.google.com/file/d/{copied_id}/view")
                
                # Determine file type for nice output
                file_type = "File"
                if 'spreadsheet' in mime_type:
                    file_type = "Spreadsheet"
                elif 'document' in mime_type:
                    file_type = "Document"
                elif 'presentation' in mime_type:
                    file_type = "Presentation"
                
                output = f"✅ {file_type} copied successfully!\n\n"
                output += f"📄 {copied_name}\n"
                output += f"🔗 {copied_link}\n"
                
                if destination_folder:
                    output += f"📁 Saved to: {destination_folder}\n"
                
                output += f"\nAll formatting, formulas, and styles preserved."
                
                return output
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"❌ Error copying file: {str(e)}"
        
        tools.extend([list_drive_files, search_drive_files, get_drive_file_content, read_pdf_from_drive, create_drive_folder, upload_file_to_folder, copy_file])
        print(f"[Google Tools] Loaded 7 Drive tools")
        
    except Exception as e:
        print(f"[Google Tools] Failed to create Drive tools: {e}")
    
    return tools


def create_sheets_tools(credentials) -> List[Any]:
    """Create Google Sheets tools with user's credentials."""
    tools = []
    
    try:
        service = build('sheets', 'v4', credentials=credentials)
        
        @tool
        def read_spreadsheet(spreadsheet_id: str, range_name: str = "Sheet1!A1:Z100") -> str:
            """Read data from a Google Spreadsheet. Provide the spreadsheet ID and optional range (default: Sheet1!A1:Z100)."""
            try:
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, 
                    range=range_name
                ).execute()
                values = result.get('values', [])
                if not values:
                    return "The spreadsheet is empty or range not found."
                
                # Format as table
                output = []
                for i, row in enumerate(values[:30]):  # Limit to 30 rows
                    output.append(" | ".join(str(cell) for cell in row))
                return "\n".join(output)
            except Exception as e:
                return f"Error reading spreadsheet: {str(e)}"
        
        @tool
        def get_spreadsheet_info(spreadsheet_id: str) -> str:
            """Get information about a Google Spreadsheet (title, sheet names, etc)."""
            try:
                result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                title = result.get('properties', {}).get('title', 'Unknown')
                sheets = [s['properties']['title'] for s in result.get('sheets', [])]
                return f"Spreadsheet: {title}\nSheets: {', '.join(sheets)}"
            except Exception as e:
                return f"Error getting spreadsheet info: {str(e)}"
        
        @tool
        def write_to_spreadsheet(spreadsheet_id: str, range_name: str, values: str) -> str:
            """Write data to a Google Spreadsheet. Values should be comma-separated, rows separated by semicolons. Example: 'A,B,C;1,2,3'"""
            try:
                # Parse the values string
                rows = []
                for row_str in values.split(';'):
                    rows.append([cell.strip() for cell in row_str.split(',')])
                
                body = {'values': rows}
                result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                return f"Successfully updated {result.get('updatedCells', 0)} cells."
            except Exception as e:
                return f"Error writing to spreadsheet: {str(e)}"
        
        @tool
        def create_spreadsheet(title: str) -> str:
            """Create a new Google Spreadsheet with the given title."""
            try:
                spreadsheet = {'properties': {'title': title}}
                spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
                return f"Spreadsheet created with ID: {spreadsheet.get('spreadsheetId')}"
            except Exception as e:
                return f"Error creating spreadsheet: {str(e)}"

        @tool
        def add_expense_row(date: str, merchant: str, total: str, category: str = "Uncategorized") -> str:
            """
            Add an expense row to the 'Expenses' sheet.
            Arguments:
            - date: Date of purchase (e.g., '2025-01-05')
            - merchant: Name of the merchant (e.g., 'Starbucks')
            - total: Total amount (e.g., '45.00')
            - category: Optional category (default: 'Uncategorized')
            """
            try:
                # Find or create 'Expenses' sheet
                import datetime
                
                # Search for a sheet named "Expenses"
                query = "name = 'Expenses' and mimeType = 'application/vnd.google-apps.spreadsheet'"
                results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                files = results.get('files', [])
                
                if not files:
                    # Create new sheet if not found
                    spreadsheet = {'properties': {'title': 'Expenses'}}
                    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
                    spreadsheet_id = spreadsheet.get('spreadsheetId')
                    
                    # Add header row
                    header = [['Date', 'Merchant', 'Total', 'Category', 'Added At']]
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id, 
                        range='Sheet1!A1', 
                        valueInputOption='RAW', 
                        body={'values': header}
                    ).execute()
                else:
                    spreadsheet_id = files[0]['id']
                    
                # Append row
                added_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                values = [[date, merchant, total, category, added_at]]
                
                service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!A:E',
                    valueInputOption='USER_ENTERED',
                    body={'values': values}
                ).execute()
                
                return f"✅ Added expense to 'Expenses' sheet: {merchant} - ${total}"
            except Exception as e:
                return f"Error adding expense: {str(e)}"

        tools.extend([read_spreadsheet, get_spreadsheet_info, write_to_spreadsheet, create_spreadsheet, add_expense_row])
        print(f"[Google Tools] Loaded 5 Sheets tools")
        
    except Exception as e:
        print(f"[Google Tools] Failed to create Sheets tools: {e}")
    
    return tools


def create_calendar_tools(credentials) -> List[Any]:
    """Create Google Calendar tools with user's credentials."""
    tools = []
    
    try:
        service = build('calendar', 'v3', credentials=credentials)
        
        @tool
        def list_calendar_events(days_ahead: int = 1) -> str:
            """
            List upcoming calendar events.
            
            Args:
                days_ahead: Number of days to look ahead. Use 0 or 1 for today only, 7 for a week, etc.
            
            Returns:
                List of upcoming events with dates and times
            """
            try:
                import datetime
                
                # Malaysia timezone: UTC+8 (hardcoded, doesn't depend on server locale)
                MY_TZ = datetime.timezone(datetime.timedelta(hours=8))
                now_my = datetime.datetime.now(MY_TZ)
                
                # Start from the BEGINNING of today to catch all events for today
                start_of_today = now_my.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # If days_ahead is 0 or 1, show today's events. Otherwise, add the days.
                if days_ahead <= 1:
                    end_my = start_of_today + datetime.timedelta(days=1)  # End of today
                else:
                    end_my = start_of_today + datetime.timedelta(days=days_ahead)
                
                # Convert to RFC3339 format for Google Calendar API
                time_min = start_of_today.isoformat()
                time_max = end_my.isoformat()
                
                print(f"[Calendar] Querying events from {time_min} to {time_max}")
                
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=20,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                if not events:
                    if days_ahead <= 1:
                        return "No events scheduled for today."
                    else:
                        return f"No events in the next {days_ahead} days."
                
                output = []
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    summary = event.get('summary', 'No title')
                    location = event.get('location', '')
                    loc_str = f" @ {location}" if location else ""
                    
                    # Format the time nicely
                    try:
                        if 'T' in start:  # DateTime format
                            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                            time_str = dt.strftime("%b %d, %H:%M")
                        else:  # All-day event
                            time_str = f"{start} (All day)"
                    except:
                        time_str = start
                    
                    output.append(f"📅 {time_str}: {summary}{loc_str}")
                
                return "\n".join(output)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"Error listing events: {str(e)}"
        
        @tool
        def create_calendar_event(summary: str, start_datetime: str, end_datetime: str, location: str = "", description: str = "") -> str:
            """
            Create a new calendar event.
            
            Args:
                summary: Title of the event (e.g. "Meeting with Jason")
                start_datetime: Start time in ISO format (e.g. "2024-01-07T16:00:00")
                end_datetime: End time in ISO format (e.g. "2024-01-07T17:00:00")
                location: Optional location (e.g. "Ativo Plaza Damansara")
                description: Optional description
            
            Returns:
                Success or error message
            """
            try:
                event = {
                    'summary': summary,
                    'location': location,
                    'description': description,
                    'start': {
                        'dateTime': start_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur',
                    },
                    'end': {
                        'dateTime': end_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur',
                    },
                }
                
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                
                return f"✅ Created event: {summary}\n📍 {location if location else 'No location'}\n🕐 {start_datetime}\nEvent ID: {created_event.get('id')}"
            except Exception as e:
                return f"❌ Error creating event: {str(e)}"
        
        tools.extend([list_calendar_events, create_calendar_event])
        print(f"[Google Tools] Loaded 2 Calendar tools")
        
    except Exception as e:
        print(f"[Google Tools] Failed to create Calendar tools: {e}")
    
    return tools
