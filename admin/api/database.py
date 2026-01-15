from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Get project root (two levels up from admin/api)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'bot.db')}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class InviteCode(Base):
    __tablename__ = "invite_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    telegram_id = Column(Integer, nullable=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="invite", uselist=False)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    invite_id = Column(Integer, ForeignKey("invite_codes.id"), nullable=True)
    is_allowed = Column(Boolean, default=True)
    voice_enabled = Column(Boolean, default=False)
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    invite = relationship("InviteCode", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")


class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    file_name = Column(String, nullable=True)
    bot_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_logs")


class UserPreference(Base):
    """Stores user preferences for quotation system (template, folder, etc.)"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    template_file_id = Column(String, nullable=True)          # Google Doc ID for quotation template
    quotation_folder_id = Column(String, nullable=True)       # Drive folder for PDFs
    log_sheet_id = Column(String, nullable=True)              # Quotation log Sheet ID
    email_cc = Column(String, nullable=True)                  # Default CC email
    quotation_validity_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCatalogue(Base):
    """Stores user's catalogues (multiple per user)"""
    __tablename__ = "user_catalogues"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)                     # e.g., "Products", "Services"
    file_type = Column(String, nullable=False)                # "pdf" or "sheet"
    drive_file_id = Column(String, nullable=True)             # Google Drive file ID
    chroma_collection = Column(String, nullable=True)         # ChromaDB collection name
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotationLog(Base):
    """Tracks all quotations created by users"""
    __tablename__ = "quotation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=False)
    quotation_number = Column(String, nullable=False)         # QT-YYYYMMDD-XXX
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)
    items_json = Column(Text, nullable=True)                  # JSON array of items
    total = Column(String, nullable=True)
    pdf_file_id = Column(String, nullable=True)               # Google Drive PDF ID
    status = Column(String, default="pending")                # pending, sent, cancelled
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Run migrations for new columns
    from sqlalchemy import text
    with engine.connect() as conn:
        # Add voice_enabled column if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN voice_enabled BOOLEAN DEFAULT 0"))
            conn.commit()
            print("[DB] Added voice_enabled column to users table")
        except Exception:
            pass  # Column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
