"""
Catalogue Tools - Upload, index, and search product/service catalogues.
Supports PDF catalogues via Gemini Vision extraction and Google Sheets.
"""

import os
import json
import io
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from .google_auth import get_credentials
from .memory import memory_manager


# FAISS persistence directory (same as memory.py)
FAISS_PERSIST_DIR = os.getenv("FAISS_PERSIST_DIR", "/app/data/faiss")


class CatalogueIndex:
    """LangChain FAISS-based index for catalogue items."""
    
    def __init__(self, telegram_id: int, catalogue_id: int):
        self.telegram_id = telegram_id
        self.catalogue_id = catalogue_id
        self.index_dir = os.path.join(FAISS_PERSIST_DIR, f"catalogue_{telegram_id}_{catalogue_id}")
        
        os.makedirs(FAISS_PERSIST_DIR, exist_ok=True)
        
        # Get embedding function from memory module
        from .memory import GoogleEmbeddings
        self.embedding_fn = GoogleEmbeddings()
        
        # Initialize or load vector store
        self.vector_store = None
        self._load()
    
    def _load(self):
        """Load existing index from disk."""
        try:
            from langchain_community.vectorstores import FAISS
            
            if os.path.exists(self.index_dir):
                self.vector_store = FAISS.load_local(
                    self.index_dir,
                    self.embedding_fn,
                    allow_dangerous_deserialization=True
                )
                print(f"[Catalogue] Loaded FAISS index for catalogue {self.catalogue_id}")
        except Exception as e:
            print(f"[Catalogue] Error loading index: {e}")
            self.vector_store = None
    
    def _save(self):
        """Save index to disk."""
        if self.vector_store:
            try:
                self.vector_store.save_local(self.index_dir)
            except Exception as e:
                print(f"[Catalogue] Error saving index: {e}")
    
    def add_items(self, items: List[Dict]):
        """Add items to the index."""
        if not items:
            return
        
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_core.documents import Document
            
            # Create documents with metadata
            docs = []
            for item in items:
                content = f"{item.get('name', '')} {item.get('description', '')} {item.get('item_code', '')}"
                doc = Document(page_content=content, metadata=item)
                docs.append(doc)
            
            if self.vector_store is None:
                # Create new vector store
                self.vector_store = FAISS.from_documents(docs, self.embedding_fn)
            else:
                # Add to existing
                self.vector_store.add_documents(docs)
            
            self._save()
            print(f"[Catalogue] Indexed {len(items)} items")
        except Exception as e:
            print(f"[Catalogue] Error adding items: {e}")
            import traceback
            traceback.print_exc()
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search the catalogue."""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=n_results)
            
            formatted = []
            for doc, score in results:
                formatted.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": score
                })
            return formatted
        except Exception as e:
            print(f"[Catalogue] Error searching: {e}")
            return []
    
    def clear(self):
        """Clear the index."""
        try:
            import shutil
            if os.path.exists(self.index_dir):
                shutil.rmtree(self.index_dir)
            self.vector_store = None
        except Exception as e:
            print(f"[Catalogue] Error clearing: {e}")


def get_catalogue_index(telegram_id: int, catalogue_id: int) -> CatalogueIndex:
    """Get a catalogue index for a user."""
    return CatalogueIndex(telegram_id, catalogue_id)


def extract_items_from_pdf_with_vision(pdf_bytes: bytes, telegram_id: int) -> List[Dict]:
    """
    Use Gemini Vision to extract items from PDF catalogue.
    Converts PDF pages to images and sends to Gemini for extraction.
    """
    try:
        from google import genai
        import fitz  # PyMuPDF for PDF to image conversion
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[Catalogue] No GEMINI_API_KEY found")
            return []
        
        client = genai.Client(api_key=api_key)
        
        # Open PDF and convert pages to images
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_items = []
        
        extraction_prompt = """
Analyze this catalogue page and extract ALL items/products you can find.
For each item, extract:
- item_code: Product code/SKU if available (or null)
- name: Product/item name
- description: Description if available (or null)
- price: Price if available (or null)
- unit: Unit of measure if available (or null)

Return ONLY a valid JSON array of objects. Example:
[
  {"item_code": "ABC123", "name": "Widget Pro", "description": "Premium widget", "price": "99.00", "unit": "piece"},
  {"item_code": null, "name": "Basic Tool", "description": null, "price": "25.00", "unit": null}
]

If no items found, return empty array: []
"""
        
        for page_num in range(min(len(doc), 20)):  # Limit to 20 pages
            page = doc[page_num]
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_bytes = pix.tobytes("png")
            
            # Send to Gemini Vision
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-05-20",
                    contents=[
                        {"inline_data": {"mime_type": "image/png", "data": img_bytes}},
                        extraction_prompt
                    ]
                )
                
                # Parse response
                text = response.text.strip()
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                items = json.loads(text)
                if isinstance(items, list):
                    for item in items:
                        item["page"] = page_num + 1
                    all_items.extend(items)
                    print(f"[Catalogue] Page {page_num + 1}: Extracted {len(items)} items")
                    
            except json.JSONDecodeError as e:
                print(f"[Catalogue] Page {page_num + 1}: JSON parse error - {e}")
            except Exception as e:
                print(f"[Catalogue] Page {page_num + 1}: Error - {e}")
        
        doc.close()
        return all_items
        
    except ImportError:
        print("[Catalogue] PyMuPDF (fitz) not installed. Install with: pip install pymupdf")
        return []
    except Exception as e:
        print(f"[Catalogue] Error extracting from PDF: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_catalogue_tools(telegram_id: int) -> list:
    """
    Create catalogue management tools for a specific user.
    """
    
    credentials = get_credentials(telegram_id)
    if not credentials:
        return []
    
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"[Catalogue] Error building Drive service: {e}")
        return []
    
    @tool
    def save_catalogue(catalogue_name: str, folder_name: str = "") -> str:
        """
        Save the PDF catalogue that the user just sent.
        Use this when user sends a PDF file and says to save it as a catalogue.
        The file must have been sent in the current message.
        
        Args:
            catalogue_name: Name for this catalogue (e.g., "Home Inventory", "Products")
            folder_name: Optional folder name to save the catalogue in (creates folder if doesn't exist)
        
        Returns:
            Success message with item count or error
        """
        # Get file context from agent
        from bot.config import telegram_agent
        file_context = telegram_agent.get_current_file_context(telegram_id)
        
        if not file_context:
            return "❌ No file found in the current message. Please send a PDF file with your save instruction."
        
        file_bytes, filename, mime_type = file_context
        
        # Validate it's a PDF
        if mime_type != "application/pdf":
            return f"❌ The file you sent is not a PDF (it's {mime_type}). Please send a PDF catalogue."
        
        # Call the actual save function
        success, message = save_catalogue_from_pdf(
            telegram_id=telegram_id,
            pdf_bytes=file_bytes,
            catalogue_name=catalogue_name,
            original_filename=filename,
            folder_name=folder_name
        )
        
        return message
    
    @tool
    def list_catalogues() -> str:
        """
        List all catalogues saved for this user.
        
        Returns:
            List of catalogue names and details
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, file_type, created_at FROM user_catalogues WHERE telegram_id = ?",
                (telegram_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "📂 You don't have any catalogues saved yet.\n\nTo add one, send me a PDF file and say 'Save this as my Products catalogue' (or any name you prefer)."
            
            output = "📂 Your Catalogues:\n\n"
            for row in rows:
                cat_id, name, file_type, created = row
                output += f"• {name} ({file_type.upper()}) - ID: {cat_id}\n"
            
            output += "\nUse 'search catalogue for [item name]' to find items."
            return output
            
        except Exception as e:
            return f"❌ Error listing catalogues: {str(e)}"
    
    @tool
    def search_catalogue(
        query: str,
        catalogue_name: Optional[str] = None
    ) -> str:
        """
        Search for items in the user's catalogues using semantic search.
        Use this when user asks about product prices, availability, or details.
        
        Args:
            query: What to search for (item name, description, code)
            catalogue_name: Optional specific catalogue to search (search all if not provided)
        
        Returns:
            Matching items with details
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get user's catalogues
            if catalogue_name:
                cursor.execute(
                    "SELECT id, name FROM user_catalogues WHERE telegram_id = ? AND name LIKE ?",
                    (telegram_id, f"%{catalogue_name}%")
                )
            else:
                cursor.execute(
                    "SELECT id, name FROM user_catalogues WHERE telegram_id = ?",
                    (telegram_id,)
                )
            
            catalogues = cursor.fetchall()
            conn.close()
            
            if not catalogues:
                return "❌ No catalogues found. Upload a PDF catalogue first using 'Save this as my [Name] catalogue'"
            
            # Search in FAISS indices
            all_results = []
            for cat_id, cat_name in catalogues:
                try:
                    cat_index = get_catalogue_index(telegram_id, cat_id)
                    results = cat_index.search(query, n_results=5)
                    
                    for r in results:
                        if r.get("distance", 100) < 1.5:  # Relevance threshold
                            all_results.append({
                                "catalogue": cat_name,
                                "content": r["content"],
                                "metadata": r["metadata"],
                                "distance": r["distance"]
                            })
                except Exception as e:
                    print(f"[Catalogue] Error searching catalogue {cat_id}: {e}")
            
            if not all_results:
                return f"❌ No items found matching '{query}' in your catalogues."
            
            # Sort by relevance
            all_results.sort(key=lambda x: x['distance'])
            
            output = f"🔍 Found {len(all_results)} item(s) matching '{query}':\n\n"
            for result in all_results[:10]:  # Limit to top 10
                meta = result['metadata']
                output += f"📦 {meta.get('name', 'Unknown Item')}\n"
                if meta.get('item_code'):
                    output += f"   Code: {meta['item_code']}\n"
                if meta.get('price'):
                    output += f"   Price: ${meta['price']}\n"
                if meta.get('description'):
                    output += f"   {meta['description'][:100]}\n"
                output += f"   (from: {result['catalogue']})\n\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Error searching catalogues: {str(e)}"
    
    @tool
    def delete_catalogue(catalogue_name: str) -> str:
        """
        Delete a catalogue by name. Removes from Drive and database.
        
        Args:
            catalogue_name: Name of the catalogue to delete
        
        Returns:
            Success or error message
        """
        try:
            import sqlite3
            from bot.config import DATABASE_PATH
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Find the catalogue
            cursor.execute(
                "SELECT id, drive_file_id FROM user_catalogues WHERE telegram_id = ? AND name LIKE ?",
                (telegram_id, f"%{catalogue_name}%")
            )
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return f"❌ Catalogue '{catalogue_name}' not found."
            
            cat_id, drive_file_id = row
            
            # Delete from Drive
            if drive_file_id:
                try:
                    drive_service.files().delete(fileId=drive_file_id).execute()
                except Exception as e:
                    print(f"[Catalogue] Error deleting from Drive: {e}")
            
            # Delete FAISS index
            try:
                cat_index = get_catalogue_index(telegram_id, cat_id)
                cat_index.clear()
            except Exception as e:
                print(f"[Catalogue] Error deleting index: {e}")
            
            # Delete from database
            cursor.execute("DELETE FROM user_catalogues WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            
            return f"✅ Catalogue '{catalogue_name}' deleted successfully."
            
        except Exception as e:
            return f"❌ Error deleting catalogue: {str(e)}"
    
    return [save_catalogue, list_catalogues, search_catalogue, delete_catalogue]


def save_catalogue_from_pdf(
    telegram_id: int,
    pdf_bytes: bytes,
    catalogue_name: str,
    original_filename: str,
    folder_name: str = ""
) -> tuple:
    """
    Save a PDF catalogue: upload to Drive, extract items, index to ChromaDB.
    Called from processor.py when user sends a PDF with save instruction.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        import sqlite3
        from bot.config import DATABASE_PATH
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        
        credentials = get_credentials(telegram_id)
        if not credentials:
            return False, "❌ Please connect your Google account first with /register_google"
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Handle folder creation if requested
        folder_id = None
        if folder_name:
            # Check if folder exists
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = drive_service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                print(f"[Catalogue] Using existing folder: {folder_name} ({folder_id})")
            else:
                # Create the folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')
                print(f"[Catalogue] Created folder: {folder_name} ({folder_id})")
        
        # Step 1: Upload PDF to Google Drive
        print(f"[Catalogue] Uploading {original_filename} to Drive...")
        
        # Use catalogue name directly, avoid redundant naming
        file_name = f"{catalogue_name}.pdf"
        
        file_metadata = {
            'name': file_name,
            'mimeType': 'application/pdf'
        }
        
        # Add to folder if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaIoBaseUpload(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        drive_file_id = file.get('id')
        print(f"[Catalogue] Uploaded to Drive: {drive_file_id}")
        
        # Step 2: Extract items using Gemini Vision
        print(f"[Catalogue] Extracting items from PDF...")
        items = extract_items_from_pdf_with_vision(pdf_bytes, telegram_id)
        print(f"[Catalogue] Extracted {len(items)} items")
        
        if not items:
            # Still save reference even if no items extracted
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_catalogues (telegram_id, name, file_type, drive_file_id, created_at)
                VALUES (?, ?, 'pdf', ?, datetime('now'))
            """, (telegram_id, catalogue_name, drive_file_id))
            conn.commit()
            conn.close()
            
            return True, f"📁 Catalogue '{catalogue_name}' saved to Drive.\n\n⚠️ Could not extract items automatically. You may need to upload a clearer PDF or a Google Sheet instead."
        
        # Step 3: Save to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if catalogue with same name exists
        cursor.execute(
            "SELECT id FROM user_catalogues WHERE telegram_id = ? AND name = ?",
            (telegram_id, catalogue_name)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            catalogue_id = existing[0]
            cursor.execute("""
                UPDATE user_catalogues 
                SET drive_file_id = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (drive_file_id, catalogue_id))
        else:
            # Create new
            cursor.execute("""
                INSERT INTO user_catalogues (telegram_id, name, file_type, drive_file_id, created_at)
                VALUES (?, ?, 'pdf', ?, datetime('now'))
            """, (telegram_id, catalogue_name, drive_file_id))
            catalogue_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Step 4: Index items to FAISS
        print(f"[Catalogue] Indexing {len(items)} items to FAISS...")
        cat_index = get_catalogue_index(telegram_id, catalogue_id)
        
        # Prepare items with proper format
        indexed_items = []
        for item in items:
            indexed_items.append({
                "item_code": item.get('item_code') or "",
                "name": item.get('name') or "",
                "description": item.get('description') or "",
                "price": item.get('price') or "",
                "unit": item.get('unit') or "",
                "page": str(item.get('page', 1))
            })
        
        # Add to FAISS index
        cat_index.add_items(indexed_items)
        
        print(f"[Catalogue] Indexed {len(items)} items successfully")
        
        return True, f"✅ Catalogue '{catalogue_name}' saved!\n\n📊 Extracted {len(items)} items from {original_filename}\n📁 Uploaded to Google Drive\n🔍 Ready for search\n\nTry: 'Search catalogue for [item name]'"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"❌ Error saving catalogue: {str(e)}"
