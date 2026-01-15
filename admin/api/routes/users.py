from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db, User, InviteCode
from ..models import UserResponse, UserUpdate
from ..auth import verify_token

router = APIRouter(prefix="/users", tags=["users"])


def get_current_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    try:
        # Use joinedload to eagerly load the invite relationship
        from sqlalchemy.orm import joinedload
        users = db.query(User).options(joinedload(User.invite)).order_by(User.created_at.desc()).all()
        
        # Import Google auth check
        try:
            from agent.google_auth import has_google_credentials
        except ImportError:
            def has_google_credentials(uid): return False
            
        result = []
        for user in users:
            invite_name = None
            if user.invite_id:
                try:
                    if user.invite:
                        invite_name = user.invite.name
                except Exception:
                    pass  # Handle cases where invite is deleted
            
            # Check Google connection status
            is_google_connected = has_google_credentials(user.telegram_id)
            
            user_dict = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_allowed": user.is_allowed,
                "last_activity": user.last_activity,
                "created_at": user.created_at,
                "invite_name": invite_name,
                "is_google_connected": is_google_connected  # Added field
            }
            # Note: We need to update UserResponse model too, but for now passing as dict
            # The Pydantic model might strip it if strict, let's update models.py next
            result.append(user_dict)
        return result
    except Exception as e:
        # Log the error for debugging
        print(f"Error in list_users: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update: UserUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update.is_allowed is not None:
        user.is_allowed = update.is_allowed
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_allowed=user.is_allowed,
        last_activity=user.last_activity,
        created_at=user.created_at,
        invite_name=user.invite.name if user.invite else None
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
