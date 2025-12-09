"""
Resend Email Backend for Django
Uses Resend API instead of SMTP (works on Railway without port restrictions)
"""
import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """
    Django email backend that uses Resend API instead of SMTP.
    
    Perfect for Railway deployment since it doesn't require SMTP ports.
    Uses HTTP API calls which are never blocked by cloud providers.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY not configured in settings")
            logger.error("❌ RESEND_API_KEY not configured")
        else:
            # Import resend here to avoid unused import warning
            import resend
            resend.api_key = self.api_key
            logger.info("✅ Resend API configured successfully")
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        
        if not self.api_key:
            logger.error("❌ Cannot send emails - RESEND_API_KEY not configured")
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            except Exception as e:
                logger.error(f"❌ Failed to send email via Resend: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return num_sent
    
    def _send(self, message):
        """Send a single EmailMessage via Resend API"""
        if not message.recipients():
            logger.warning("⚠️ Email message has no recipients")
            return False
        
        try:
            # Prepare email data for Resend API
            from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
            
            # Extract email address from "Name <email@example.com>" format
            if '<' in from_email and '>' in from_email:
                from_email = from_email.split('<')[1].split('>')[0].strip()
            
            email_data = {
                'from': from_email,
                'to': message.to,
                'subject': message.subject,
            }
            
            # Add CC and BCC if present
            if message.cc:
                email_data['cc'] = message.cc
            if message.bcc:
                email_data['bcc'] = message.bcc
            
            # Add reply_to if present
            if message.reply_to:
                email_data['reply_to'] = message.reply_to
            
            # Handle HTML and plain text content
            if message.content_subtype == 'html':
                email_data['html'] = message.body
            else:
                email_data['text'] = message.body
            
            # If there are alternatives (like HTML version of plain text email)
            for alternative in message.alternatives:
                content, mimetype = alternative
                if mimetype == 'text/html':
                    email_data['html'] = content
            
            # Send via Resend API
            logger.info(f"📧 Sending email via Resend to: {', '.join(message.to)}")
            logger.info(f"   Subject: {message.subject}")
            
            import resend
            response = resend.Emails.send(email_data)
            
            logger.info(f"✅ Email sent successfully via Resend | ID: {response.get('id', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Resend API error: {str(e)}")
            if not self.fail_silently:
                raise
            return False
