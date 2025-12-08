"""
Multi-Service Email Backend with Automatic Rotation
Rotates between multiple free email services to achieve high volume without limits
"""

import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.conf import settings
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RotatingEmailBackend(BaseEmailBackend):
    """
    Intelligent email backend that rotates between multiple free SMTP services
    to maximize free email quota across multiple providers.
    
    Supported services:
    - Brevo: 300 emails/day
    - Elastic Email: 100 emails/day
    - Mailgun: 167 emails/day (5000/month)
    - SendGrid: 100 emails/day
    
    Total: ~667 emails/day = 20,000/month FREE!
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = self._load_services()
        self.current_service_index = 0
        
    def _load_services(self):
        """
        Load all configured email services from environment variables
        Format: SERVICE_NAME_HOST, SERVICE_NAME_PORT, etc.
        """
        services = []
        
        # Brevo (300/day)
        if os.environ.get('BREVO_SMTP_HOST'):
            services.append({
                'name': 'Brevo',
                'host': os.environ.get('BREVO_SMTP_HOST', 'smtp-relay.brevo.com'),
                'port': int(os.environ.get('BREVO_SMTP_PORT', 587)),
                'username': os.environ.get('BREVO_SMTP_USER'),
                'password': os.environ.get('BREVO_SMTP_PASSWORD'),
                'use_tls': True,
                'use_ssl': False,
                'daily_limit': 300,
                'sent_today': 0,
                'last_reset': datetime.now().date()
            })
        
        # Elastic Email (100/day)
        if os.environ.get('ELASTIC_SMTP_HOST'):
            services.append({
                'name': 'Elastic Email',
                'host': os.environ.get('ELASTIC_SMTP_HOST', 'smtp.elasticemail.com'),
                'port': int(os.environ.get('ELASTIC_SMTP_PORT', 2525)),
                'username': os.environ.get('ELASTIC_SMTP_USER'),
                'password': os.environ.get('ELASTIC_SMTP_PASSWORD'),
                'use_tls': True,
                'use_ssl': False,
                'daily_limit': 100,
                'sent_today': 0,
                'last_reset': datetime.now().date()
            })
        
        # Mailgun (167/day ≈ 5000/month)
        if os.environ.get('MAILGUN_SMTP_HOST'):
            services.append({
                'name': 'Mailgun',
                'host': os.environ.get('MAILGUN_SMTP_HOST', 'smtp.mailgun.org'),
                'port': int(os.environ.get('MAILGUN_SMTP_PORT', 587)),
                'username': os.environ.get('MAILGUN_SMTP_USER'),
                'password': os.environ.get('MAILGUN_SMTP_PASSWORD'),
                'use_tls': True,
                'use_ssl': False,
                'daily_limit': 167,
                'sent_today': 0,
                'last_reset': datetime.now().date()
            })
        
        # SendGrid (100/day)
        if os.environ.get('SENDGRID_SMTP_HOST'):
            services.append({
                'name': 'SendGrid',
                'host': os.environ.get('SENDGRID_SMTP_HOST', 'smtp.sendgrid.net'),
                'port': int(os.environ.get('SENDGRID_SMTP_PORT', 587)),
                'username': os.environ.get('SENDGRID_SMTP_USER', 'apikey'),
                'password': os.environ.get('SENDGRID_SMTP_PASSWORD'),
                'use_tls': True,
                'use_ssl': False,
                'daily_limit': 100,
                'sent_today': 0,
                'last_reset': datetime.now().date()
            })
        
        logger.info(f"✅ Loaded {len(services)} email services for rotation")
        for service in services:
            logger.info(f"   - {service['name']}: {service['daily_limit']}/day")
        
        return services
    
    def _get_next_available_service(self):
        """
        Get the next available service that hasn't hit its daily limit
        Rotates through services to balance load
        """
        if not self.services:
            raise Exception("No email services configured for rotation!")
        
        today = datetime.now().date()
        
        # Reset counters if it's a new day
        for service in self.services:
            if service['last_reset'] != today:
                service['sent_today'] = 0
                service['last_reset'] = today
        
        # Try to find a service with available quota
        for _ in range(len(self.services)):
            service = self.services[self.current_service_index]
            
            if service['sent_today'] < service['daily_limit']:
                logger.info(f"📧 Using {service['name']} ({service['sent_today']}/{service['daily_limit']} sent today)")
                return service
            
            # This service is at limit, try next one
            self.current_service_index = (self.current_service_index + 1) % len(self.services)
            logger.debug(f"⚠️ {service['name']} at daily limit, trying next service...")
        
        # All services are at their daily limit!
        logger.error("❌ All email services have reached their daily limits!")
        raise Exception("All email services exhausted for today. Try again tomorrow.")
    
    def send_messages(self, email_messages):
        """
        Send email messages using the rotating service backend
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                # Get next available service
                service = self._get_next_available_service()
                
                # Create SMTP backend for this service
                backend = SMTPBackend(
                    host=service['host'],
                    port=service['port'],
                    username=service['username'],
                    password=service['password'],
                    use_tls=service['use_tls'],
                    use_ssl=service['use_ssl'],
                    fail_silently=False
                )
                
                # Send the message
                result = backend.send_messages([message])
                
                if result > 0:
                    service['sent_today'] += 1
                    sent_count += 1
                    logger.info(f"✅ Email sent via {service['name']} to {message.to}")
                    
                    # Move to next service for load balancing
                    self.current_service_index = (self.current_service_index + 1) % len(self.services)
                
            except Exception as e:
                logger.error(f"❌ Failed to send email to {message.to}: {str(e)}")
                if not self.fail_silently:
                    raise
        
        logger.info(f"📊 Total emails sent: {sent_count}/{len(email_messages)}")
        return sent_count
