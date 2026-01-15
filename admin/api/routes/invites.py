from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import secrets
import string

from ..database import get_db, InviteCode
from ..models import InviteCreate, InviteResponse
from ..auth import verify_token

router = APIRouter(prefix="/invites", tags=["invites"])


def get_current_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


def generate_invite_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("", response_model=List[InviteResponse])
def list_invites(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    invites = db.query(InviteCode).order_by(InviteCode.created_at.desc()).all()
    return invites


@router.post("", response_model=InviteResponse)
def create_invite(
    invite: InviteCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Generate unique code
    code = generate_invite_code()
    while db.query(InviteCode).filter(InviteCode.code == code).first():
        code = generate_invite_code()
    
    db_invite = InviteCode(
        code=code,
        name=invite.name,
        phone=invite.phone
    )
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    return db_invite


@router.delete("/{invite_id}")
def delete_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    invite = db.query(InviteCode).filter(InviteCode.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite.is_used:
        raise HTTPException(status_code=400, detail="Cannot delete used invite")
    
    db.delete(invite)
    db.commit()
    return {"message": "Invite deleted"}
