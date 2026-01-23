from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .database import init_db, get_db, AdminUser, SessionLocal
from .models import LoginRequest, TokenResponse, AdminUserResponse
from .auth import hash_password, verify_password, create_token, verify_token
from .routes.users import router as users_router
from .routes.invites import router as invites_router
from .routes.logs import router as logs_router
from .routes.google_oauth import router as google_router

app = FastAPI(title="GT-Bot Admin", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(users_router, prefix="/api")
app.include_router(invites_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(google_router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    
    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        existing = db.query(AdminUser).filter(AdminUser.username == admin_username).first()
        if not existing:
            admin = AdminUser(
                username=admin_username,
                password_hash=hash_password(admin_password)
            )
            db.add(admin)
            db.commit()
            print(f"Created admin user: {admin_username}")
    finally:
        db.close()


@app.post("/api/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.username)
    return TokenResponse(access_token=token)


@app.get("/api/auth/me", response_model=AdminUserResponse)
def get_me(authorization: str = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.split(" ")[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# Serve React static files (dist folder copied to static during build)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # All client routes - serve React SPA
    # These routes are handled by React Router on the frontend
    @app.get("/")
    @app.get("/privacy")
    @app.get("/terms")
    @app.get("/login")
    @app.get("/users")
    @app.get("/invites")
    @app.get("/logs")
    @app.get("/logs/conversation/{user_id}")
    async def serve_spa(user_id: int = None):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    
    # Catch-all for other routes (SPA routing)
    @app.get("/{path:path}")
    async def serve_react(path: str):
        # Don't intercept API calls or docs
        if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
            
        # Check if file exists in static directory (for assets)
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # All other routes go to React SPA
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

