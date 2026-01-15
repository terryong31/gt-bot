"""
Google OAuth Routes for FastAPI Admin API
Handles OAuth callback and status checking.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse
import sys
sys.path.insert(0, '/app')

router = APIRouter(prefix="/google", tags=["google"])


@router.get("/callback")
async def google_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """
    OAuth callback endpoint.
    Google redirects here after user authorizes.
    """
    try:
        # Import here to avoid circular imports
        from agent.google_auth import exchange_code
        
        success, message, telegram_id = exchange_code(code, state)
        
        if success:
            # Return a nice success page
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google Account Linked</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }}
                    .container {{
                        text-align: center;
                        padding: 40px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                    }}
                    h1 {{ font-size: 3em; margin-bottom: 10px; }}
                    p {{ font-size: 1.2em; opacity: 0.9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅</h1>
                    <h2>Google Account Linked!</h2>
                    <p>{message}</p>
                    <p>You can now close this window and return to Telegram.</p>
                </div>
            </body>
            </html>
            """)
        else:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #f06 0%, #f79 100%);
                        color: white;
                    }}
                    .container {{
                        text-align: center;
                        padding: 40px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌</h1>
                    <h2>Error Linking Account</h2>
                    <p>{message}</p>
                </div>
            </body>
            </html>
            """, status_code=400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{telegram_id}")
async def google_oauth_status(telegram_id: int):
    """
    Check if a user has linked their Google account.
    """
    try:
        from agent.google_auth import has_google_credentials
        
        return {
            "telegram_id": telegram_id,
            "linked": has_google_credentials(telegram_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
