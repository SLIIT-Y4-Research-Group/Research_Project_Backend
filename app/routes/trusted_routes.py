"""
Trusted Contact Routes
Handles invitation acceptance
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from app.services.trusted_service import get_invitation_by_token, accept_invitation

router = APIRouter(prefix="/trusted", tags=["Trusted Contacts"])

@router.get("/accept", response_class=HTMLResponse)
def accept_trusted_contact_invitation(token: str = Query(..., description="Invitation token")):
    """
    Accept a trusted contact invitation
    
    This endpoint is accessed via email link and returns HTML response
    """
    try:
        # Check if invitation exists
        invitation = get_invitation_by_token(token)
        
        if not invitation:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 50px;
                            background-color: #f8f9fa;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        .error {
                            color: #dc3545;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 class="error">❌ Invalid or Expired Invitation</h2>
                        <p>This invitation link is not valid or has expired.</p>
                        <p>Please contact the parent who sent you this invitation.</p>
                    </div>
                </body>
                </html>
                """,
                status_code=400
            )
        
        # Check if already accepted
        if invitation["status"] == "accepted":
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 50px;
                            background-color: #f8f9fa;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        .success {
                            color: #28a745;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 class="success">✅ Already Accepted</h2>
                        <p>You have already accepted this invitation.</p>
                        <p>You will receive alert emails when the child's mood patterns show concerning trends (with their consent).</p>
                    </div>
                </body>
                </html>
                """
            )
        
        # Accept the invitation
        success = accept_invitation(token)
        
        if success:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 50px;
                            background-color: #f8f9fa;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        .success {
                            color: #28a745;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 class="success">✅ Invitation Accepted!</h2>
                        <p>Thank you for accepting to be a trusted contact.</p>
                        <p>You will now receive mental health alert emails if the child shows concerning mood patterns (when they give consent).</p>
                        <p>Your support can make a real difference in the child's well-being.</p>
                        <p style="margin-top: 30px; font-size: 14px; color: #666;">
                            You can close this window now.
                        </p>
                    </div>
                </body>
                </html>
                """
            )
        else:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 50px;
                            background-color: #f8f9fa;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        .error {
                            color: #dc3545;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 class="error">❌ Error</h2>
                        <p>Unable to accept invitation. Please try again later.</p>
                    </div>
                </body>
                </html>
                """,
                status_code=500
            )
            
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .error {{
                        color: #dc3545;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2 class="error">❌ Error</h2>
                    <p>An unexpected error occurred.</p>
                    <p style="font-size: 12px; color: #666;">{str(e)}</p>
                </div>
            </body>
            </html>
            """,
            status_code=500
        )
