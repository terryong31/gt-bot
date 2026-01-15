from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime
import os
import math

from ..database import get_db, ChatLog, User
from ..models import ChatLogResponse, PaginatedLogs
from ..auth import verify_token

router = APIRouter(prefix="/logs", tags=["logs"])

# Container structure: /app/admin/api/routes/logs.py -> need to go up to /app/
# dirname x3 to get from routes/logs.py -> routes -> api -> admin, then up to /app
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "data", "uploads")




def get_current_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    """Get a list of all conversations grouped by user"""
    # Get all users who have chat logs
    users_with_logs = db.query(
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name
    ).join(ChatLog).distinct().all()
    
    conversations = []
    for user in users_with_logs:
        # Get message count for this user
        message_count = db.query(ChatLog).filter(ChatLog.user_id == user.id).count()
        
        # Get last message
        last_log = db.query(ChatLog).filter(
            ChatLog.user_id == user.id
        ).order_by(desc(ChatLog.created_at)).first()
        
        # Get last message preview (truncate if too long)
        last_message = None
        if last_log:
            if last_log.message_type == 'text' and last_log.content:
                last_message = last_log.content[:50] + "..." if len(last_log.content) > 50 else last_log.content
            else:
                last_message = f"📎 {last_log.message_type.title() if last_log.message_type else 'File'}"
        
        user_name = user.first_name or user.username or f"User {user.telegram_id}"
        
        conversations.append({
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "user_name": user_name,
            "message_count": message_count,
            "last_message": last_message,
            "last_activity": last_log.created_at if last_log else None
        })
    
    # Sort by last activity
    conversations.sort(key=lambda x: x["last_activity"] or datetime.min, reverse=True)
    
    return conversations


@router.get("", response_model=PaginatedLogs)
def list_logs(
    user_id: Optional[int] = None,
    message_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    query = db.query(ChatLog)
    
    if user_id:
        query = query.filter(ChatLog.user_id == user_id)
    if message_type:
        query = query.filter(ChatLog.message_type == message_type)
    if from_date:
        query = query.filter(ChatLog.created_at >= from_date)
    if to_date:
        query = query.filter(ChatLog.created_at <= to_date)
    
    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1
    
    logs = query.order_by(desc(ChatLog.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        items.append(ChatLogResponse(
            id=log.id,
            user_id=log.user_id,
            message_type=log.message_type,
            content=log.content,
            file_name=log.file_name,
            bot_response=log.bot_response,
            created_at=log.created_at,
            user_name=user.first_name or user.username if user else None
        ))
    
    return PaginatedLogs(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{log_id}/media")
def get_media(
    log_id: int,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Verify token from either header or query parameter
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    elif token:
        auth_token = token
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    username = verify_token(auth_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    log = db.query(ChatLog).filter(ChatLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if not log.content or log.message_type == "text":
        raise HTTPException(status_code=400, detail="No media file for this log")
    
    file_path = os.path.join(UPLOADS_DIR, log.content)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=log.file_name or "file")


@router.get("/conversations/{user_id}/messages")
def get_conversation_messages(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    """Get all messages for a specific user conversation"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get total count
    total = db.query(ChatLog).filter(ChatLog.user_id == user_id).count()
    
    # Get messages - Fetch latest first (DESC), then reverse for display
    logs = db.query(ChatLog).filter(
        ChatLog.user_id == user_id
    ).order_by(desc(ChatLog.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    # Reverse logs to maintain chronological order in the response (Oldest -> Newest)
    # This ensures the chat UI renders the context correctly
    logs.reverse()
    
    messages = []
    for log in logs:
        messages.append({
            "id": log.id,
            "sender": "user",
            "message_type": log.message_type,
            "content": log.content,
            "file_name": log.file_name,
            "created_at": log.created_at
        })
        
        # Add bot response as a separate message if it exists
        if log.bot_response:
            messages.append({
                "id": log.id,
                "sender": "bot",
                "message_type": "text",
                "content": log.bot_response,
                "file_name": None,
                "created_at": log.created_at
            })
    
    return {
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "name": user.first_name or user.username or f"User {user.telegram_id}"
        },
        "messages": messages,
        "total": total,
        "page": page,
        "limit": limit
    }
