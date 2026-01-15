"""
Quotation Tools - Generate, amend, and manage quotations.
Creates PDFs from templates, logs to sheets, and handles approval workflow.
"""

import os
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .google_auth import get_credentials


# Malaysia timezone
MYT = timezone(timedelta(hours=8))


def get_next_quotation_number(telegram_id: int) -> str:
    """Generate next quotation number: QT-YYYYMMDD-XXX"""
    import sqlite3
    from bot.config import DATABASE_PATH
    
    today = datetime.now(MYT).strftime("%Y%m%d")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Count quotations created today
    cursor.execute("""
        SELECT COUNT(*) FROM quotation_logs 
        WHERE telegram_id = ? AND quotation_number LIKE ?
    """, (telegram_id, f"QT-{today}-%"))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return f"QT-{today}-{count + 1:03d}"


def get_quotation_tools(telegram_id: int) -> list:
    """
    Create quotation management tools for a specific user.
    """
    
    credentials = get_credentials(telegram_id)
    if not credentials:
        return []
    
    try:
        # Build services with default settings (timeout is handled by retry logic)
        drive_service = build('drive', 'v3', credentials=credentials)
        docs_service = build('docs', 'v1', credentials=credentials)
        sheets_service = build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"[Quotation] Error building services: {e}")
        return []
    
    @tool
    def create_quotation(
        customer_name: str,
        customer_email: Optional[str],
        items: str,
        customer_company: Optional[str] = None,
        customer_phone: Optional[str] = None,
        notes: Optional[str] = None,
        validity_days: int = 30
    ) -> str:
        """
        Create a new quotation for a customer.
        Use this when user wants to generate a quotation/quote for someone.
        
        Args:
            customer_name: Customer's full name
            customer_email: Customer's email address (for sending)
            items: Items to quote, format: "Item1 x quantity @ price, Item2 x quantity @ price"
                   Example: "Widget A x 10 @ $50, Widget B x 5 @ $25"
            customer_company: Customer's company name (optional)
            customer_phone: Customer's phone number (optional)
            notes: Additional notes for the quotation (optional)
            validity_days: How many days the quote is valid (default: 30)
        
        Returns:
            Quotation summary and next steps (approve/amend/cancel)
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            # Get user preferences
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT template_file_id, quotation_folder_id, log_sheet_id, quotation_validity_days
                FROM user_preferences WHERE telegram_id = ?
            """, (telegram_id,))
            
            prefs = cursor.fetchone()
            
            if not prefs or not prefs[0]:
                conn.close()
                return ("❌ No quotation template configured.\n\n"
                        "Please set up your quotation template first:\n"
                        "1. Create a Google Doc with your template\n"
                        "2. Tell me: 'Set my quotation template to [Doc name or URL]'")
            
            template_id, folder_id, log_sheet_id, default_validity = prefs
            validity_days = validity_days or default_validity or 30
            
            # Generate quotation number
            quotation_number = get_next_quotation_number(telegram_id)
            today = datetime.now(MYT)
            valid_until = today + timedelta(days=validity_days)
            
            # Parse items
            parsed_items = []
            total = 0.0
            
            for item_str in items.split(","):
                item_str = item_str.strip()
                if not item_str:
                    continue
                
                # Try to parse "Item x quantity @ price"
                parts = item_str.lower().replace("x", " x ").replace("@", " @ ").split()
                
                item_name = []
                quantity = 1
                price = 0.0
                
                mode = "name"
                for part in parts:
                    if part == "x" and mode == "name":
                        mode = "qty"
                    elif part == "@":
                        mode = "price"
                    elif mode == "name":
                        item_name.append(part)
                    elif mode == "qty":
                        try:
                            quantity = int(part)
                        except:
                            pass
                    elif mode == "price":
                        try:
                            price = float(part.replace("$", "").replace(",", ""))
                        except:
                            pass
                
                item_total = quantity * price
                total += item_total
                
                parsed_items.append({
                    "name": " ".join(item_name).title(),
                    "quantity": quantity,
                    "price": price,
                    "total": item_total
                })
            
            if not parsed_items:
                conn.close()
                return "❌ Could not parse items. Please format like: 'Item A x 10 @ $50, Item B x 5 @ $25'"
            
            # ============================================
            # Create quotation document programmatically
            # ============================================
            
            # Create a new Google Doc
            doc_title = f"Quotation {quotation_number}"
            new_doc = docs_service.documents().create(body={'title': doc_title}).execute()
            new_doc_id = new_doc['documentId']
            
            # Move to quotation folder if specified
            if folder_id:
                drive_service.files().update(
                    fileId=new_doc_id,
                    addParents=folder_id,
                    removeParents='root'
                ).execute()
            
            # Get user's company info from the template (try to extract header info)
            company_header = "Your Company"
            try:
                template_doc = docs_service.documents().get(documentId=template_id).execute()
                template_text = ""
                for element in template_doc.get('body', {}).get('content', []):
                    if 'paragraph' in element:
                        for text_run in element['paragraph'].get('elements', []):
                            if 'textRun' in text_run:
                                template_text += text_run['textRun'].get('content', '')
                
                # Try to extract company info from first few lines
                lines = [l.strip() for l in template_text.split('\n') if l.strip()]
                if lines:
                    company_header = lines[0]
            except Exception as e:
                print(f"[Quotation] Could not read template header: {e}")
            
            # Build document content
            content_lines = []
            
            # Header
            content_lines.append(company_header)
            content_lines.append("")
            content_lines.append("QUOTATION")
            content_lines.append("")
            
            # Customer and date info
            content_lines.append(f"Quotation for:                                    Date: {today.strftime('%B %d, %Y')}")
            content_lines.append(f"Mr./Ms. {customer_name}                           Quotation #: {quotation_number}")
            if customer_company:
                content_lines.append(f"{customer_company}                             Valid until: {valid_until.strftime('%B %d, %Y')}")
            else:
                content_lines.append(f"                                                  Valid until: {valid_until.strftime('%B %d, %Y')}")
            content_lines.append("")
            
            # Items header
            content_lines.append("━" * 70)
            content_lines.append(f"{'No.':<5} {'Description':<30} {'Qty':<8} {'Unit Price':<12} {'Total':<12}")
            content_lines.append("━" * 70)
            
            # Items
            for i, item in enumerate(parsed_items, 1):
                content_lines.append(
                    f"{i:<5} {item['name']:<30} {item['quantity']:<8} ${item['price']:<11,.2f} ${item['total']:<11,.2f}"
                )
            
            # Empty rows for spacing
            content_lines.append("")
            content_lines.append("━" * 70)
            
            # Total
            content_lines.append(f"{'Total Quoted Amount:':<57} ${total:,.2f}")
            content_lines.append("━" * 70)
            content_lines.append("")
            
            # Terms and conditions
            content_lines.append("Terms & Conditions:")
            content_lines.append("• 50% deposit to begin. Balance payable upon completion.")
            content_lines.append("• Price includes labor and materials.")
            content_lines.append(f"• This quotation is valid for {validity_days} days.")
            if notes:
                content_lines.append(f"• {notes}")
            content_lines.append("")
            content_lines.append("Thank you for your business!")
            
            # Join all content
            full_content = "\n".join(content_lines)
            
            # Build requests for document update
            requests = []
            
            # Insert the content
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': full_content
                }
            })
            
            # Apply formatting - Title "QUOTATION" should be bold and larger
            title_start = full_content.find("QUOTATION") + 1
            title_end = title_start + len("QUOTATION")
            
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': title_start, 'endIndex': title_end},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 18, 'unit': 'PT'}
                    },
                    'fields': 'bold,fontSize'
                }
            })
            
            # Header should be bold
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(company_header) + 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 12, 'unit': 'PT'}
                    },
                    'fields': 'bold,fontSize'
                }
            })
            
            # Set monospace font for the table section (for alignment)
            table_start = full_content.find("━") + 1
            table_end = full_content.rfind("━") + 2
            
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': table_start, 'endIndex': table_end},
                    'textStyle': {
                        'weightedFontFamily': {'fontFamily': 'Courier New'}
                    },
                    'fields': 'weightedFontFamily'
                }
            })
            
            # Execute all formatting requests
            if requests:
                docs_service.documents().batchUpdate(
                    documentId=new_doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Export as PDF with retry logic
            import time
            max_retries = 3
            pdf_response = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    pdf_response = drive_service.files().export(
                        fileId=new_doc_id,
                        mimeType='application/pdf'
                    ).execute()
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    print(f"[Quotation] PDF export attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff: 1, 2, 4 seconds
            
            if not pdf_response:
                # Cleanup the failed Google Doc
                try:
                    drive_service.files().delete(fileId=new_doc_id).execute()
                except:
                    pass
                conn.close()
                return f"❌ Failed to generate PDF after {max_retries} attempts. Google API may be temporarily unavailable. Please try again in a moment."
            
            # Upload PDF
            pdf_metadata = {
                "name": f"{quotation_number}.pdf",
                "parents": [folder_id] if folder_id else []
            }
            
            pdf_media = MediaIoBaseUpload(
                io.BytesIO(pdf_response),
                mimetype='application/pdf'
            )
            
            pdf_file = drive_service.files().create(
                body=pdf_metadata,
                media_body=pdf_media,
                fields='id,webViewLink'
            ).execute()
            
            pdf_id = pdf_file.get("id")
            pdf_link = pdf_file.get("webViewLink")
            
            # Delete the temp Doc (keep only PDF)
            drive_service.files().delete(fileId=new_doc_id).execute()
            
            # Log to database
            cursor.execute("""
                INSERT INTO quotation_logs 
                (telegram_id, quotation_number, customer_name, customer_email, customer_company,
                 items_json, total, pdf_file_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
            """, (
                telegram_id, quotation_number, customer_name, customer_email,
                customer_company, json.dumps(parsed_items), total, pdf_id
            ))
            
            quotation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Build response
            items_summary = "\n".join([f"  • {item['name']} x {item['quantity']} = ${item['total']:.2f}" for item in parsed_items])
            
            return f"""📄 Quotation {quotation_number} Created!

👤 Customer: {customer_name}
   {f"Email: {customer_email}" if customer_email else ""}
   {f"Company: {customer_company}" if customer_company else ""}

📦 Items:
{items_summary}

💰 Total: ${float(total):,.2f}
⏰ {f"Valid for {validity_days} days"}

📁 PDF: {pdf_link}

What would you like to do?
✅ "Send this quotation to the customer" - Email to {customer_email or 'customer'}
✏️ "Change [item] quantity to [X]" - Amend and regenerate
❌ "Cancel this quotation" - Delete PDF and record"""
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error creating quotation: {str(e)}"
    
    
    @tool
    def upload_and_set_quotation_template(template_name: Optional[str] = None) -> str:
        """
        Upload the DOCX file that the user just sent and set it as the quotation template.
        Use this when user sends a .docx file and says it's the quotation template.
        
        Args:
            template_name: Optional custom name for the template (default: use original filename)
        
        Returns:
            Success message or error
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH, telegram_agent
            
            # Get file context from agent
            file_context = telegram_agent.get_current_file_context(telegram_id)
            
            if not file_context:
                return "❌ No file found in the current message. Please send a DOCX file with your instruction."
            
            file_bytes, filename, mime_type = file_context
            
            # Validate it's a DOCX
            if mime_type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                return f"❌ The file you sent is not a Word document (it's {mime_type}). Please send a .docx file."
            
            # Use provided name or original filename
            final_name = template_name or filename.replace('.docx', '').replace('.doc', '')
            
            # Upload to Drive and convert to Google Doc
            file_metadata = {
                'name': final_name,
                'mimeType': 'application/vnd.google-apps.document'  # Convert to Google Doc
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype=mime_type,
                resumable=True
            )
            
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name'
            ).execute()
            
            file_id = uploaded_file.get('id')
            doc_name = uploaded_file.get('name')
            
            # Save as template preference
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (telegram_id, template_file_id, created_at, updated_at)
                VALUES (?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(telegram_id) DO UPDATE SET 
                    template_file_id = excluded.template_file_id,
                    updated_at = datetime('now')
            """, (telegram_id, file_id))
            
            conn.commit()
            conn.close()
            
            return f"""✅ Quotation template uploaded and set!

📄 Template: {doc_name}
📁 Uploaded to Google Drive and converted to Google Doc

Your template should have placeholders like:
{{{{customer_name}}}}, {{{{items_table}}}}, {{{{total}}}}, {{{{quotation_number}}}}, {{{{date}}}}

You can now create quotations using this template!"""
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error uploading template: {str(e)}"
    
    @tool
    def set_quotation_template(template_identifier: str) -> str:
        """
        Set the quotation template to an existing Google Doc.
        Use this when user references a Google Doc that's already in their Drive.
        
        Args:
            template_identifier: Name or URL of the Google Doc to use as template
        
        Returns:
            Success or error message
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            # Search for the document in Drive
            query = f"name contains '{template_identifier}' and mimeType = 'application/vnd.google-apps.document'"
            
            # If it looks like a URL, extract the ID
            if "docs.google.com" in template_identifier:
                import re
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', template_identifier)
                if match:
                    file_id = match.group(1)
                    # Verify it exists
                    try:
                        doc = drive_service.files().get(fileId=file_id).execute()
                        template_name = doc.get('name', template_identifier)
                    except:
                        return "❌ Could not access that document. Make sure it's a Google Doc you own."
                else:
                    return "❌ Invalid Google Docs URL"
            else:
                results = drive_service.files().list(
                    q=query,
                    pageSize=5,
                    fields="files(id, name)"
                ).execute()
                
                files = results.get('files', [])
                if not files:
                    return f"❌ No Google Doc found matching '{template_identifier}'"
                
                if len(files) > 1:
                    file_list = "\n".join([f"  • {f['name']}" for f in files])
                    return f"Found multiple documents:\n{file_list}\n\nPlease be more specific or share the Doc URL."
                
                file_id = files[0]['id']
                template_name = files[0]['name']
            
            # Save preference
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (telegram_id, template_file_id, created_at, updated_at)
                VALUES (?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(telegram_id) DO UPDATE SET 
                    template_file_id = excluded.template_file_id,
                    updated_at = datetime('now')
            """, (telegram_id, file_id))
            
            conn.commit()
            conn.close()
            
            return f"✅ Quotation template set to: {template_name}\n\nYour template should have placeholders like:\n{{{{customer_name}}}}, {{{{items_table}}}}, {{{{total}}}}, {{{{quotation_number}}}}, {{{{date}}}}"
            
        except Exception as e:
            return f"❌ Error setting template: {str(e)}"
    
    @tool
    def set_quotation_folder(folder_identifier: str) -> str:
        """
        Set the folder where quotation PDFs will be saved.
        Use this when user says 'save quotations to...' or 'set quotation folder to...'
        
        Args:
            folder_identifier: Name or URL of the Google Drive folder
        
        Returns:
            Success or error message
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            # Search for the folder
            if "drive.google.com" in folder_identifier:
                import re
                match = re.search(r'/folders/([a-zA-Z0-9_-]+)', folder_identifier)
                if match:
                    folder_id = match.group(1)
                    try:
                        folder = drive_service.files().get(fileId=folder_id).execute()
                        folder_name = folder.get('name', folder_identifier)
                    except:
                        return "❌ Could not access that folder."
                else:
                    return "❌ Invalid Google Drive folder URL"
            else:
                query = f"name contains '{folder_identifier}' and mimeType = 'application/vnd.google-apps.folder'"
                results = drive_service.files().list(
                    q=query,
                    pageSize=5,
                    fields="files(id, name)"
                ).execute()
                
                files = results.get('files', [])
                if not files:
                    return f"❌ No folder found matching '{folder_identifier}'"
                
                folder_id = files[0]['id']
                folder_name = files[0]['name']
            
            # Save preference
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (telegram_id, quotation_folder_id, created_at, updated_at)
                VALUES (?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(telegram_id) DO UPDATE SET 
                    quotation_folder_id = excluded.quotation_folder_id,
                    updated_at = datetime('now')
            """, (telegram_id, folder_id))
            
            conn.commit()
            conn.close()
            
            return f"✅ Quotation folder set to: {folder_name}\n\nAll quotation PDFs will be saved here."
            
        except Exception as e:
            return f"❌ Error setting folder: {str(e)}"
    
    @tool
    def list_quotations(status: Optional[str] = None) -> str:
        """
        List user's quotations, optionally filtered by status.
        
        Args:
            status: Filter by status (pending, sent, cancelled) or None for all
        
        Returns:
            List of quotations
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT quotation_number, customer_name, total, status, created_at
                    FROM quotation_logs WHERE telegram_id = ? AND status = ?
                    ORDER BY created_at DESC LIMIT 10
                """, (telegram_id, status))
            else:
                cursor.execute("""
                    SELECT quotation_number, customer_name, total, status, created_at
                    FROM quotation_logs WHERE telegram_id = ?
                    ORDER BY created_at DESC LIMIT 10
                """, (telegram_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "📋 No quotations found."
            
            output = "📋 Your Quotations:\n\n"
            for row in rows:
                qn, customer, total, st, created = row
                status_icon = {"pending": "⏳", "sent": "✅", "cancelled": "❌"}.get(st, "❓")
                output += f"{status_icon} {qn} - {customer} - ${float(total):,.2f}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error listing quotations: {str(e)}"
    
    @tool
    def cancel_quotation(quotation_number: str) -> str:
        """
        Cancel a quotation - deletes the PDF and removes the log entry.
        Use this when user rejects a quotation.
        
        Args:
            quotation_number: The quotation number to cancel (e.g., QT-20260107-001)
        
        Returns:
            Success or error message
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, pdf_file_id FROM quotation_logs
                WHERE telegram_id = ? AND quotation_number = ?
            """, (telegram_id, quotation_number))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return f"❌ Quotation {quotation_number} not found."
            
            quote_id, pdf_id = row
            
            # Delete PDF from Drive
            if pdf_id:
                try:
                    drive_service.files().delete(fileId=pdf_id).execute()
                    print(f"[Quotation] Deleted PDF {pdf_id}")
                except Exception as e:
                    print(f"[Quotation] Error deleting PDF: {e}")
            
            # Delete from database
            cursor.execute("DELETE FROM quotation_logs WHERE id = ?", (quote_id,))
            conn.commit()
            conn.close()
            
            return f"✅ Quotation {quotation_number} cancelled and deleted."
            
        except Exception as e:
            return f"❌ Error cancelling quotation: {str(e)}"
    
    @tool
    def send_quotation_email(
        quotation_number: str,
        cc_email: Optional[str] = None
    ) -> str:
        """
        Send a quotation to the customer via email with the PDF attached.
        Use this when user approves sending the quotation.
        
        Args:
            quotation_number: The quotation to send (e.g., QT-20260107-001)
            cc_email: Optional CC email address
        
        Returns:
            Success or error message
        """
        try:
            import sqlite3
            import base64
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            from bot.config import DATABASE_PATH
            
            # Get quotation details
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, customer_name, customer_email, customer_company, total, pdf_file_id
                FROM quotation_logs WHERE telegram_id = ? AND quotation_number = ?
            """, (telegram_id, quotation_number))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return f"❌ Quotation {quotation_number} not found."
            
            quote_id, customer_name, customer_email, customer_company, total, pdf_id = row
            
            if not customer_email:
                conn.close()
                return "❌ No email address for this customer. Cannot send."
            
            if not pdf_id:
                conn.close()
                return "❌ PDF file not found. Please regenerate the quotation."
            
            # Download PDF from Drive
            request = drive_service.files().get_media(fileId=pdf_id)
            pdf_data = io.BytesIO()
            downloader = MediaIoBaseDownload(pdf_data, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            pdf_bytes = pdf_data.getvalue()
            
            # Build Gmail service
            gmail_service = build('gmail', 'v1', credentials=credentials)
            
            # Create email
            msg = MIMEMultipart()
            msg['To'] = customer_email
            msg['Subject'] = f"Quotation {quotation_number} - Your Requested Quote"
            
            if cc_email:
                msg['Cc'] = cc_email
            
            # Professional email body
            company_name = customer_company or "your company"
            body = f"""Dear {customer_name},

Thank you for your interest in our products/services.

Please find attached our quotation ({quotation_number}) for your review. 

Quotation Total: ${float(total):,.2f}

This quotation is valid for 30 days from the date of issue. Should you have any questions or require further clarification, please do not hesitate to contact us.

We look forward to the opportunity to serve you.

Best regards"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            part = MIMEBase('application', 'pdf')
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{quotation_number}.pdf"')
            msg.attach(part)
            
            # Send email
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Update quotation status
            cursor.execute("""
                UPDATE quotation_logs SET status = 'sent', updated_at = datetime('now')
                WHERE id = ?
            """, (quote_id,))
            conn.commit()
            conn.close()
            
            cc_note = f"\n📋 CC'd to: {cc_email}" if cc_email else ""
            
            return f"""✅ Quotation {quotation_number} sent!

📧 Sent to: {customer_email}{cc_note}
📄 Attached: {quotation_number}.pdf
💰 Amount: ${float(total):,.2f}

The quotation status has been updated to 'Sent'."""
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error sending quotation: {str(e)}"
    
    return [
        create_quotation,
        upload_and_set_quotation_template,
        set_quotation_template,
        set_quotation_folder,
        list_quotations,
        cancel_quotation,
        send_quotation_email
    ]
