"""
Per-user vector memory using LangChain FAISS with Google Embeddings.
Each user gets their own index for persistent semantic memory.
Supports RAG-style semantic retrieval for context-aware responses.
"""

import os
from typing import Optional, List, Dict

# FAISS persistence directory
FAISS_PERSIST_DIR = os.getenv("FAISS_PERSIST_DIR", "/app/data/faiss")


class GoogleEmbeddings:
    """LangChain-compatible embeddings using Google GenAI."""
    
    def __init__(self):
        self.client = None
        self.dimension = 768
        self._init_client()
    
    def _init_client(self):
        """Initialize the Google GenAI client."""
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[Memory] Could not init Google client: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        if not self.client or not texts:
            return [[0.0] * self.dimension] * len(texts)
        
        try:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts
            )
            return [emb.values for emb in response.embeddings]
        except Exception as e:
            print(f"[Memory] Batch embedding error: {e}")
            return [[0.0] * self.dimension] * len(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        if not self.client:
            return [0.0] * self.dimension
        
        try:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"[Memory] Query embedding error: {e}")
            return [0.0] * self.dimension
    
    def __call__(self, texts):
        """Make the class callable for compatibility with FAISS."""
        if isinstance(texts, str):
            return self.embed_query(texts)
        return self.embed_documents(texts)


def get_embedding_function():
    """Get the embedding function for FAISS."""
    return GoogleEmbeddings()


class UserMemory:
    """Manages vector memory for a specific user with LangChain FAISS."""
    
    def __init__(self, user_id: int, persist_dir: str = FAISS_PERSIST_DIR, embedding_fn=None):
        self.user_id = user_id
        self.persist_dir = persist_dir
        self.embedding_fn = embedding_fn or GoogleEmbeddings()
        self.index_dir = os.path.join(persist_dir, f"user_{user_id}")
        
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize or load the FAISS vector store
        self.vector_store = None
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing index or create a new one."""
        try:
            from langchain_community.vectorstores import FAISS
            
            if os.path.exists(self.index_dir):
                # Load existing index
                self.vector_store = FAISS.load_local(
                    self.index_dir,
                    self.embedding_fn,
                    allow_dangerous_deserialization=True
                )
                print(f"[Memory] Loaded FAISS index for user {self.user_id}")
            else:
                # Create new empty index - need at least one document to initialize
                self.vector_store = None  # Will be created on first add
                print(f"[Memory] New FAISS index will be created for user {self.user_id}")
        except Exception as e:
            print(f"[Memory] Error loading FAISS: {e}")
            self.vector_store = None
    
    def add_message(self, message: str, role: str = "user", metadata: Optional[Dict] = None):
        """Add a message to the user's memory."""
        if not message or len(message.strip()) < 10:
            return
        
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_core.documents import Document
            
            msg_metadata = {"role": role, **(metadata or {})}
            doc = Document(page_content=message, metadata=msg_metadata)
            
            if self.vector_store is None:
                # Create new vector store with first document
                self.vector_store = FAISS.from_documents([doc], self.embedding_fn)
            else:
                # Add to existing
                self.vector_store.add_documents([doc])
            
            # Save to disk
            self._save()
        except Exception as e:
            print(f"[Memory] Error adding to memory: {e}")
    
    def _save(self):
        """Save the vector store to disk."""
        if self.vector_store:
            try:
                self.vector_store.save_local(self.index_dir)
            except Exception as e:
                print(f"[Memory] Error saving: {e}")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant memories based on semantic similarity."""
        if not query or not self.vector_store:
            return []
        
        try:
            # Use similarity_search_with_score for distance info
            results = self.vector_store.similarity_search_with_score(query, k=n_results)
            
            formatted = []
            for doc, score in results:
                formatted.append({
                    "content": doc.page_content,
                    "role": doc.metadata.get("role", "unknown"),
                    "distance": score  # Lower is better for L2
                })
            return formatted
        except Exception as e:
            print(f"[Memory] Error searching: {e}")
            return []
    
    def get_recent(self, n: int = 10) -> List[str]:
        """Get most recent messages from memory."""
        # FAISS doesn't track order, so return empty
        return []
    
    def clear(self):
        """Clear all memories for this user."""
        try:
            import shutil
            if os.path.exists(self.index_dir):
                shutil.rmtree(self.index_dir)
            self.vector_store = None
        except Exception as e:
            print(f"[Memory] Error clearing: {e}")
    
    @property
    def count(self) -> int:
        """Get number of memories stored."""
        if self.vector_store:
            try:
                return self.vector_store.index.ntotal
            except:
                return 0
        return 0


class MemoryManager:
    """Manages memory for all users with RAG retrieval."""
    
    def __init__(self, persist_dir: str = FAISS_PERSIST_DIR):
        self.persist_dir = persist_dir
        self._memories: Dict[int, UserMemory] = {}
        self._embedding_fn = GoogleEmbeddings()
        print(f"[Memory] Initialized with FAISS + Google embeddings")
    
    def get_user_memory(self, user_id: int) -> UserMemory:
        """Get or create memory for a user."""
        if user_id not in self._memories:
            self._memories[user_id] = UserMemory(
                user_id, 
                self.persist_dir,
                self._embedding_fn
            )
        return self._memories[user_id]
    
    def add_conversation(self, user_id: int, user_message: str, bot_response: str):
        """Add a conversation exchange to user's memory."""
        memory = self.get_user_memory(user_id)
        # Combine for better context
        combined = f"User asked: {user_message}\nAssistant replied: {bot_response[:500]}"
        memory.add_message(combined, role="conversation")
    
    def get_context(self, user_id: int, query: str, n_results: int = 5) -> str:
        """Get relevant context from user's memory using RAG retrieval."""
        memory = self.get_user_memory(user_id)
        relevant = memory.search(query, n_results)
        
        if not relevant:
            return ""
        
        # Filter by relevance (distance threshold - lower is better for L2)
        filtered = [r for r in relevant if r.get("distance", 100) < 1.5]
        
        if not filtered:
            return ""
        
        context = "📚 Relevant past conversations:\n"
        for item in filtered[:3]:  # Limit to top 3
            content = item["content"]
            # Truncate if too long
            if len(content) > 300:
                content = content[:300] + "..."
            context += f"- {content}\n\n"
        
        return context
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get memory statistics for a user."""
        memory = self.get_user_memory(user_id)
        return {
            "user_id": user_id,
            "memory_count": memory.count,
            "has_embeddings": True,
            "backend": "LangChain FAISS"
        }


# Global memory manager instance
memory_manager = MemoryManager()
