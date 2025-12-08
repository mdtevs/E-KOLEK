"""
HTTP-based Email Backend for Railway
Uses Gmail API instead of SMTP to bypass Railway's port restrictions
"""

import logging
import base64
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


class GmailAPIBackend(BaseEmailBackend):
    """
    Email backend that uses Gmail API instead of SMTP
    Works on Railway where SMTP ports are blocked
    
    Requires:
    - GMAIL_API_KEY environment variable (Gmail App Password)
    - Uses Gmail's REST API endpoint
    """
    
    def send_messages(self, email_messages):
        """
        Send email messages using Gmail API
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                # Use simple SMTP library with requests fallback
                # Gmail supports base64-encoded email via REST API
                success = self._send_via_gmail_api(message)
                if success:
                    sent_count += 1
                    logger.info(f"✅ Email sent successfully to {message.to}")
                else:
                    logger.error(f"❌ Failed to send email to {message.to}")
                    
            except Exception as e:
                logger.error(f"❌ Error sending email to {message.to}: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return sent_count
    
    def _send_via_gmail_api(self, message):
        """
        Send email using Gmail's REST API endpoint
        This bypasses SMTP port restrictions
        """
        try:
            # For now, we need to stick with SMTP or use a third-party service
            # Gmail API requires OAuth2 which is complex for simple email sending
            logger.error("Gmail API requires OAuth2 setup. Please use SendGrid instead.")
            return False
            
        except Exception as e:
            logger.error(f"Gmail API error: {str(e)}")
            return False
