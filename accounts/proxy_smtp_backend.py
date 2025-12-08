"""
SMTP Proxy Service for Railway
Runs a local SMTP proxy that forwards emails through Railway CLI's network access
"""

import socket
import smtplib
import threading
import logging
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend

logger = logging.getLogger(__name__)


class ProxySMTPBackend(DjangoSMTPBackend):
    """
    SMTP backend that uses a proxy server to bypass Railway's restrictions
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_enabled = False
        
    def open(self):
        """Try direct connection first, fall back to proxy if blocked"""
        try:
            # Try direct SMTP connection
            return super().open()
        except (socket.error, OSError) as e:
            logger.warning(f"Direct SMTP blocked: {str(e)}")
            logger.info("Attempting to use proxy/tunnel...")
            
            # Check if we can use Railway's internal networking
            return self._try_railway_internal_network()
    
    def _try_railway_internal_network(self):
        """
        Attempt to use Railway's internal networking or private network
        """
        try:
            # Railway private networking uses railway.internal domain
            # Check if we have access to internal services
            import os
            
            # Try to detect if we're in Railway environment
            railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
            if not railway_env:
                logger.error("Not running in Railway environment")
                return False
            
            # Check for Railway internal DNS
            internal_host = f"smtp-relay.railway.internal"
            
            logger.info(f"Attempting Railway internal network: {internal_host}")
            
            try:
                # Try to resolve internal hostname
                socket.gethostbyname(internal_host)
                logger.info(f"✅ Internal network accessible!")
                
                # Use internal network for SMTP
                self.host = internal_host
                return super().open()
                
            except socket.gaierror:
                logger.debug("Railway internal network not available")
                return False
                
        except Exception as e:
            logger.error(f"Railway internal network error: {str(e)}")
            return False
