"""
Smart Email Backend for Railway
Automatically handles SMTP connection issues with multiple fallback strategies
"""

import logging
import smtplib
import socket
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class ResilientSMTPBackend(DjangoSMTPBackend):
    """
    Enhanced SMTP backend that tries multiple ports and configurations
    to work around Railway's network restrictions
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_attempts = []
        
    def _try_connection(self, host, port, use_ssl, use_tls, timeout=None):
        """Try to connect with specific configuration"""
        try:
            logger.info(f"🔌 Attempting SMTP connection: {host}:{port} (SSL={use_ssl}, TLS={use_tls})")
            
            if use_ssl:
                # SSL connection (port 465)
                import ssl
                context = ssl.create_default_context()
                connection = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                # Regular connection with optional TLS
                connection = smtplib.SMTP(host, port, timeout=timeout)
                if use_tls:
                    connection.ehlo()
                    connection.starttls()
                    connection.ehlo()
            
            # Test connection
            connection.noop()
            logger.info(f"✅ SMTP connection successful: {host}:{port}")
            return connection
            
        except (socket.error, smtplib.SMTPException, OSError) as e:
            logger.debug(f"❌ Connection failed: {host}:{port} - {str(e)}")
            return None
    
    def open(self):
        """
        Open connection with automatic fallback to alternative ports
        Tries multiple configurations to find one that works on Railway
        """
        if self.connection:
            return False
        
        # Get configured settings
        host = self.host or 'smtp.gmail.com'
        timeout = self.timeout
        user = self.username
        password = self.password
        
        # Port configurations to try (in order of preference)
        # Port 2525 is often allowed as alternative SMTP port
        port_configs = [
            # Try configured port first
            {'port': self.port, 'use_ssl': self.use_ssl, 'use_tls': self.use_tls},
            
            # Alternative configurations for Railway
            {'port': 2525, 'use_ssl': False, 'use_tls': True},  # Alternative SMTP port (often works!)
            {'port': 587, 'use_ssl': False, 'use_tls': True},   # Standard STARTTLS
            {'port': 465, 'use_ssl': True, 'use_tls': False},   # SSL
            {'port': 8025, 'use_ssl': False, 'use_tls': True},  # Alternative port
            {'port': 25, 'use_ssl': False, 'use_tls': False},   # Plain SMTP
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_configs = []
        for config in port_configs:
            key = (config['port'], config['use_ssl'], config['use_tls'])
            if key not in seen:
                seen.add(key)
                unique_configs.append(config)
        
        # Try each configuration
        logger.info(f"🔍 Trying {len(unique_configs)} SMTP configurations for {host}")
        
        for i, config in enumerate(unique_configs, 1):
            port = config['port']
            use_ssl = config['use_ssl']
            use_tls = config['use_tls']
            
            connection = self._try_connection(host, port, use_ssl, use_tls, timeout)
            
            if connection:
                # Connection successful, now authenticate
                try:
                    if user and password:
                        connection.login(user, password)
                        logger.info(f"✅ SMTP authentication successful")
                    
                    self.connection = connection
                    
                    # Log successful configuration for admin reference
                    logger.info("="*70)
                    logger.info("🎉 WORKING SMTP CONFIGURATION FOUND!")
                    logger.info(f"   Host: {host}")
                    logger.info(f"   Port: {port}")
                    logger.info(f"   SSL: {use_ssl}")
                    logger.info(f"   TLS: {use_tls}")
                    logger.info("="*70)
                    
                    return True
                    
                except smtplib.SMTPAuthenticationError as e:
                    logger.error(f"❌ SMTP authentication failed: {str(e)}")
                    connection.quit()
                except Exception as e:
                    logger.error(f"❌ SMTP error during auth: {str(e)}")
                    try:
                        connection.quit()
                    except:
                        pass
        
        # All attempts failed - this shouldn't happen if Railway allows SMTP
        logger.error("="*70)
        logger.error("❌ ALL SMTP CONNECTION ATTEMPTS FAILED")
        logger.error(f"   Tried {len(unique_configs)} different configurations")
        logger.error(f"   Host: {host}")
        logger.error("   Ports tried: 2525, 587, 465, 8025, 25")
        logger.error("")
        logger.error("   NEXT STEPS TO DEBUG:")
        logger.error("   1. Check Railway network settings")
        logger.error("   2. Verify EMAIL_HOST_PASSWORD is correct")
        logger.error("   3. Check if Gmail requires 'Less secure apps' enabled")
        logger.error("   4. Contact Railway support for SMTP port access")
        logger.error("="*70)
        
        # Return False to indicate connection failed
        return False
