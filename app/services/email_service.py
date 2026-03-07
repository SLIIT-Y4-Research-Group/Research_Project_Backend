"""
Email Service
Handles sending emails via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from app.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL, BACKEND_BASE_URL

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_trusted_contact_invitation(to_email: str, child_name: str, token: str) -> bool:
    """
    Send trusted contact invitation email
    
    Args:
        to_email: Trusted contact email
        child_name: Name of the child
        token: Invitation token
        
    Returns:
        True if sent successfully, False otherwise
    """
    accept_url = f"{BACKEND_BASE_URL}/trusted/accept?token={token}"
    
    subject = f"Trusted Contact Invitation for {child_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Trusted Contact Invitation</h2>
            <p>Hello,</p>
            <p>You have been invited to be a trusted contact for <strong>{child_name}</strong>'s mental health monitoring system.</p>
            <p>As a trusted contact, you will receive alert emails if the child shows concerning mood patterns (with their consent).</p>
            <p>Click the button below to accept this invitation:</p>
            <a href="{accept_url}" class="button">Accept Invitation</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #0066cc;">{accept_url}</p>
            <div class="footer">
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_body)

def send_mood_alert(recipients: List[str], child_name: str, bad_mood_count: int) -> bool:
    """
    Send mood alert email to parent and trusted contacts
    
    Args:
        recipients: List of email addresses
        child_name: Name of the child
        bad_mood_count: Number of bad moods in last 7 days
        
    Returns:
        True if all emails sent successfully, False otherwise
    """
    subject = f"Mental Health Alert: {child_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .alert-box {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚠️ Mental Health Alert</h2>
            <p>Hello,</p>
            <p>This is an important notification regarding <strong>{child_name}</strong>.</p>
            <div class="alert-box">
                <p><strong>Alert Reason:</strong> The child has recorded <strong>{bad_mood_count} "Bad" moods</strong> in the last 7 days.</p>
                <p>This may indicate that the child is experiencing difficulties and could benefit from additional support or conversation.</p>
            </div>
            <p><strong>Recommended Actions:</strong></p>
            <ul>
                <li>Have a gentle, supportive conversation with the child</li>
                <li>Ask about their day and any challenges they may be facing</li>
                <li>Consider professional counseling if concerns persist</li>
            </ul>
            <div class="footer">
                <p>You are receiving this email because you are listed as a parent or trusted contact for {child_name}. The child has given consent to share this information.</p>
                <p>This is an automated alert from the Mental Health Monitoring System.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    all_sent = True
    for email in recipients:
        if not send_email(email, subject, html_body):
            all_sent = False
    
    return all_sent

def send_trusted_contact_removed_email(to_email: str, child_name: str, reason: str) -> bool:
    """
    Send email notification when removed as trusted contact
    
    Args:
        to_email: Trusted contact email
        child_name: Name of the child
        reason: Reason for removal
        
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Removed as Trusted Contact"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .info-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #6c757d;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Trusted Contact Notification</h2>
            <p>Hello,</p>
            <p>This is to inform you that you have been removed as a trusted contact for <strong>{child_name}</strong>'s mental health monitoring system.</p>
            <div class="info-box">
                <p><strong>Reason for removal:</strong></p>
                <p>{reason}</p>
            </div>
            <p>You will no longer receive alert notifications for this child.</p>
            <p>If you have any questions or concerns, please contact the child's parent directly.</p>
            <div class="footer">
                <p>This is an automated notification from the Mental Health Monitoring System.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_body)
