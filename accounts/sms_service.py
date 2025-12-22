"""
SMS Service for E-KOLEK System
Handles sending SMS notifications via iProg Tech SMS API
"""

import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any
import urllib.parse

logger = logging.getLogger(__name__)


class SMSService:
    """
    Production-ready SMS service for sending notifications via iProg Tech SMS API
    """
    
    def __init__(self):
        self.api_url = getattr(settings, 'SMS_API_URL', 'https://www.iprogsms.com/api/v1/sms_messages')
        self.api_token = getattr(settings, 'SMS_API_TOKEN', '')
        self.timeout = getattr(settings, 'SMS_API_TIMEOUT', 10)  # 10 seconds timeout
        self.enabled = getattr(settings, 'SMS_ENABLED', False)
        self.sms_provider = getattr(settings, 'SMS_PROVIDER', 2)  # Default to 2 for multi-network support
        
        if not self.api_token and self.enabled:
            logger.warning("SMS_API_TOKEN is not configured. SMS notifications will be disabled.")
            self.enabled = False
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to Philippine format (63XXXXXXXXXX)
        Accepts formats:
        - 09XXXXXXXXX -> 639XXXXXXXXX
        - 9XXXXXXXXX -> 639XXXXXXXXX
        - +639XXXXXXXXX -> 639XXXXXXXXX
        - 639XXXXXXXXX -> 639XXXXXXXXX
        """
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if phone.startswith('0'):
            # 09XXXXXXXXX -> 639XXXXXXXXX
            phone = '63' + phone[1:]
        elif phone.startswith('9') and len(phone) == 10:
            # 9XXXXXXXXX -> 639XXXXXXXXX
            phone = '63' + phone
        elif phone.startswith('63'):
            # Already in correct format
            pass
        else:
            # Invalid format, return as-is and log warning
            logger.warning(f"Unexpected phone number format: {phone}")
        
        # Validate length (should be 12 digits: 63 + 10 digits)
        if len(phone) != 12:
            logger.warning(f"Phone number has unexpected length: {phone} (length: {len(phone)})")
        
        return phone
    
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message via iProg Tech API
        
        Args:
            phone_number: Recipient's phone number (any Philippine format)
            message: SMS message content
            
        Returns:
            Dictionary with status and response data
            {
                'success': bool,
                'message_id': str (if successful),
                'error': str (if failed),
                'response': dict (full API response)
            }
        """
        if not self.enabled:
            logger.info(f"SMS disabled. Would send to {phone_number}: {message}")
            return {
                'success': False,
                'error': 'SMS service is disabled',
                'response': None
            }
        
        # Format phone number
        formatted_phone = self.format_phone_number(phone_number)
        
        # Detect network provider based on prefix
        network = "UNKNOWN"
        if formatted_phone.startswith('6390') or formatted_phone.startswith('639094') or formatted_phone.startswith('639095'):
            network = "GLOBE"
        elif formatted_phone.startswith('6391') or formatted_phone.startswith('6392') or formatted_phone.startswith('6393') or formatted_phone.startswith('6394'):
            network = "SMART/TNT"
        elif formatted_phone.startswith('639054') or formatted_phone.startswith('639053'):
            network = "SUN"
        
        logger.info(f"[NETWORK DETECTION] Detected network: {network} for {formatted_phone}")
        
        try:
            # Prepare request data with multi-network provider support
            payload = {
                'api_token': self.api_token,
                'phone_number': formatted_phone,
                'message': message,
                'sms_provider': self.sms_provider,  # Multi-network provider for all networks
                'sender_name': 'Ka Prets'  # Temporary sender name for all networks (Dec 23, 2025)
            }
            
            # Log the request (without exposing full token)
            masked_token = self.api_token[:4] + '****' if len(self.api_token) > 4 else '****'
            logger.info(f"Sending SMS to {formatted_phone} via iProg Tech API (token: {masked_token}, provider: {self.sms_provider})")
            logger.debug(f"SMS content: {message}")
            
            # Send POST request
            logger.info(f"[DEBUG] Making request to {self.api_url}")
            logger.debug(f"[DEBUG] Request payload: {{'api_token': '***', 'phone_number': '{formatted_phone}', 'message': '...', 'sms_provider': {self.sms_provider}}}")
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            # Log response details
            logger.info(f"[DEBUG] Response status code: {response.status_code}")
            logger.debug(f"[DEBUG] Response headers: {dict(response.headers)}")
            logger.debug(f"[DEBUG] Response text: {response.text}")
            
            # Parse response
            response_data = response.json()
            logger.info(f"[DEBUG] Parsed JSON response: {response_data}")
            
            # Check if successful
            if response.status_code == 200 and response_data.get('status') == 200:
                message_id = response_data.get('message_id', 'unknown')
                logger.info(f"✅ SMS sent successfully to {formatted_phone}. Message ID: {message_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'response': response_data
                }
            else:
                error_msg = response_data.get('message', 'Unknown error')
                logger.error(f"❌ SMS failed to {formatted_phone}. Status: {response.status_code}, Error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'response': response_data
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"SMS API timeout after {self.timeout} seconds"
            logger.error(f"❌ {error_msg} for {formatted_phone}")
            return {
                'success': False,
                'error': error_msg,
                'response': None
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"SMS API request failed: {str(e)}"
            logger.error(f"❌ {error_msg} for {formatted_phone}")
            return {
                'success': False,
                'error': error_msg,
                'response': None
            }
            
        except Exception as e:
            error_msg = f"Unexpected error sending SMS: {str(e)}"
            logger.exception(f"❌ {error_msg} for {formatted_phone}")
            return {
                'success': False,
                'error': error_msg,
                'response': None
            }
    
    def send_approval_notification(self, user) -> Dict[str, Any]:
        """
        Send account approval notification to user
        
        Args:
            user: Users model instance
            
        Returns:
            Dictionary with status and response data
        """
        message = (
            f"Congratulations {user.full_name}! Your E-KOLEK account has been APPROVED. "
            f"You can now log in and start earning points for proper waste segregation. "
            f"Welcome to the E-KOLEK community!"
        )
        
        return self.send_sms(user.phone, message)
    
    def send_rejection_notification(self, user, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Send account rejection notification to user
        
        Args:
            user: Users model instance
            reason: Optional reason for rejection
            
        Returns:
            Dictionary with status and response data
        """
        if reason:
            message = (
                f"Dear {user.full_name}, your E-KOLEK account registration has been REJECTED. "
                f"Reason: {reason}. Please contact CENRO office for assistance or re-register with correct information."
            )
        else:
            message = (
                f"Dear {user.full_name}, your E-KOLEK account registration has been REJECTED. "
                f"Please contact CENRO office for assistance or re-register with correct information."
            )
        
        return self.send_sms(user.phone, message)


# Singleton instance
_sms_service_instance = None


def get_sms_service() -> SMSService:
    """Get or create SMS service singleton instance"""
    global _sms_service_instance
    if _sms_service_instance is None:
        _sms_service_instance = SMSService()
    return _sms_service_instance


# Convenience functions
def send_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """Send SMS message"""
    return get_sms_service().send_sms(phone_number, message)


def send_approval_notification(user) -> Dict[str, Any]:
    """Send account approval notification"""
    return get_sms_service().send_approval_notification(user)


def send_rejection_notification(user, reason: Optional[str] = None) -> Dict[str, Any]:
    """Send account rejection notification"""
    return get_sms_service().send_rejection_notification(user, reason)
