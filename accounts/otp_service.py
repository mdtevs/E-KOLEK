import os
import requests
import logging
from django.conf import settings
import random
import string

logger = logging.getLogger(__name__)

# Load API token from environment or Django settings
# Using SMS_API_TOKEN for sending OTP via SMS API
SMS_API_TOKEN = os.environ.get('SMS_API_TOKEN') or getattr(settings, 'SMS_API_TOKEN', None)
SMS_PROVIDER = getattr(settings, 'SMS_PROVIDER', 2)  # Default to 2 for multi-network support

# iProg Tech SMS API endpoint for sending OTP
SMS_API_URL = 'https://www.iprogsms.com/api/v1/sms_messages'

# In-memory OTP storage (for verification)
# In production, consider using Redis or database for better scalability
_otp_storage = {}

# Track recently verified OTPs to prevent duplicate verification errors
# Format: {phone_number: {'verified_at': datetime, 'user_id': str}}
_recently_verified = {}



def _generate_otp(length=6):
    """Generate a random numeric OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def _store_otp(phone_number, otp_code, expires_in_minutes=5):
    """Store OTP in memory with expiration time"""
    from datetime import datetime, timedelta
    expiry = datetime.now() + timedelta(minutes=expires_in_minutes)
    _otp_storage[phone_number] = {
        'otp': otp_code,
        'expires_at': expiry,
        'attempts': 0
    }


def _verify_stored_otp(phone_number, otp_code):
    """Verify OTP from storage"""
    from datetime import datetime, timedelta
    
    # Check if this OTP was recently verified (within last 2 minutes)
    if phone_number in _recently_verified:
        verified_data = _recently_verified[phone_number]
        time_since_verify = datetime.now() - verified_data['verified_at']
        if time_since_verify < timedelta(minutes=2):
            # This OTP was just verified successfully - treat as success to avoid duplicate verification errors
            print(f"[INFO] OTP for {phone_number} was recently verified {time_since_verify.seconds}s ago - returning cached success")
            return {'success': True, 'status': 'success', 'message': 'OTP verified successfully', 'already_verified': True}
    
    if phone_number not in _otp_storage:
        return {'success': False, 'error': 'OTP not found or expired', 'error_type': 'otp_not_found'}
    
    stored_data = _otp_storage[phone_number]
    
    # Check expiration
    if datetime.now() > stored_data['expires_at']:
        del _otp_storage[phone_number]
        return {'success': False, 'error': 'OTP has expired', 'error_type': 'otp_expired'}
    
    # Check attempts
    if stored_data['attempts'] >= 3:
        del _otp_storage[phone_number]
        return {'success': False, 'error': 'Too many failed attempts', 'error_type': 'too_many_attempts'}
    
    # Verify OTP
    if stored_data['otp'] == str(otp_code):
        del _otp_storage[phone_number]  # Clear OTP after successful verification
        
        # Track this as recently verified (cache for 2 minutes)
        _recently_verified[phone_number] = {
            'verified_at': datetime.now(),
            'otp_code': otp_code
        }
        
        # Clean up old verified entries (older than 2 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=2)
        _recently_verified.clear()  # Simple cleanup - in production use Redis with TTL
        _recently_verified[phone_number] = {
            'verified_at': datetime.now(),
            'otp_code': otp_code
        }
        
        return {'success': True, 'status': 'success', 'message': 'OTP verified successfully'}
    else:
        stored_data['attempts'] += 1
        return {'success': False, 'error': 'Invalid OTP code', 'error_type': 'invalid_otp'}


def _post_json(url, payload, timeout=10):
    headers = {'Content-Type': 'application/json'}
    try:
        logger.debug(f"Making POST request to OTP API: {url}")
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        
        # Log response details at debug level
        logger.debug(f"OTP API Response - Status: {resp.status_code}")
        
        # For OTP verification, check the response even if status code indicates error
        # The API might return useful error messages in the body
        try:
            data = resp.json()
            logger.debug(f"Parsed OTP API response: {data}")
        except:
            data = {}
        
        # If we got a response with JSON, check if it has error information
        if data and isinstance(data, dict):
            # Check if API explicitly says OTP is invalid/expired
            status = str(data.get('status', '')).lower()
            message = str(data.get('message', '')).lower()
            
            # Handle invalid/expired OTP responses
            if 'invalid' in message or 'incorrect' in message or 'wrong' in message:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            elif 'expired' in message or 'expire' in message:
                return {'success': False, 'error': 'OTP code has expired. Please request a new code.', 'error_type': 'expired_otp'}
            elif status == 'error' or status == 'fail' or status == 'failed':
                error_msg = data.get('message', 'Invalid OTP code. Please try again.')
                return {'success': False, 'error': error_msg, 'error_type': 'invalid_otp'}
            elif status in ('success', 'ok'):
                data['success'] = True
                return data
        
        # Now check HTTP status code
        resp.raise_for_status()
        
        # Normalize common API shapes for successful responses
        if isinstance(data, dict):
            # If API uses 'status'/'message'
            status_value = data.get('status')
            if status_value in ('success', 'ok', '200', 200, 'OK'):
                data['success'] = True
            elif 'success' in data:
                data['success'] = bool(data.get('success'))
            else:
                # Unknown schema: assume success if HTTP 2xx
                data['success'] = True
        return data
    except requests.exceptions.HTTPError as e:
        # Parse HTTP errors and return user-friendly messages (NEVER expose API URLs)
        status_code = e.response.status_code if e.response else None
        
        # Log full error details for debugging
        print(f"[ERROR] HTTPError occurred: {e}")
        print(f"[ERROR] Status code: {status_code}")
        if e.response:
            print(f"[ERROR] Response headers: {dict(e.response.headers)}")
            print(f"[ERROR] Response text: {e.response.text}")
        
        # Check if response has JSON error details
        error_data = {}
        error_message = None
        try:
            error_data = e.response.json() if e.response else {}
            error_message = error_data.get('message') or error_data.get('error')
            print(f"[ERROR] Parsed error data: {error_data}")
            
            # Check for specific OTP error messages in the response
            if error_message:
                error_msg_lower = str(error_message).lower()
                if 'invalid' in error_msg_lower or 'incorrect' in error_msg_lower or 'wrong' in error_msg_lower:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                elif 'expired' in error_msg_lower or 'expire' in error_msg_lower:
                    return {'success': False, 'error': 'OTP code has expired. Please request a new code.', 'error_type': 'expired_otp'}
        except:
            error_message = None
        
        # If no status code (response is None), treat as connection error
        if status_code is None:
            return {'success': False, 'error': 'Unable to connect to SMS service. Please try again.', 'error_type': 'connection_error'}
        
        # Map status codes to user-friendly messages for OTP verification
        # Check if this is a verify_otp request by looking at the URL
        is_verify_request = 'verify_otp' in url if url else False
        
        if status_code == 401:
            # 401 typically means invalid OTP or expired
            if is_verify_request:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            else:
                return {'success': False, 'error': 'SMS service authentication failed. Please contact support.', 'error_type': 'auth_error'}
        elif status_code == 404:
            if is_verify_request:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            else:
                return {'success': False, 'error': 'OTP code not found or has expired. Please request a new code.', 'error_type': 'expired_otp'}
        elif status_code == 422:
            # Unprocessable entity - often means invalid input
            return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
        elif status_code == 429:
            return {'success': False, 'error': 'Too many OTP requests. Please wait a few minutes and try again.', 'error_type': 'rate_limit'}
        elif status_code == 400:
            # Bad request - check if we have a user-friendly message from API
            if error_message and not any(word in str(error_message).lower() for word in ['http', 'api', 'url', 'unauthorized']):
                return {'success': False, 'error': str(error_message), 'error_type': 'bad_request'}
            else:
                # For verify requests, assume invalid OTP
                if is_verify_request:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                else:
                    return {'success': False, 'error': 'Invalid phone number or OTP format. Please check and try again.', 'error_type': 'bad_request'}
        elif status_code >= 500:
            return {'success': False, 'error': 'SMS service is temporarily unavailable. Please try again later.', 'error_type': 'server_error'}
        else:
            # For any other HTTP error, provide generic message (never expose raw error with URLs)
            if error_message and not any(word in str(error_message).lower() for word in ['http', 'api', 'url', 'unauthorized', '401', '404', '500']):
                return {'success': False, 'error': str(error_message), 'error_type': 'api_error'}
            else:
                # Default to invalid OTP for verify requests
                if is_verify_request:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                else:
                    return {'success': False, 'error': 'Unable to process OTP request. Please try again or contact support.', 'error_type': 'api_error'}
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timeout occurred")
        return {'success': False, 'error': 'Request timeout. Please try again.', 'error_type': 'timeout'}
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Connection error occurred")
        return {'success': False, 'error': 'Connection error. Please check your internet connection.', 'error_type': 'connection_error'}
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred: {type(e).__name__}: {str(e)}")
        return {'success': False, 'error': 'An unexpected error occurred. Please try again.', 'error_type': 'unknown_error'}


def send_otp(phone_number, message=None):
    """
    Send OTP using iProg Tech SMS API
    
    API Documentation: https://www.iprogsms.com/api/v1/sms_messages
    
    Required Parameters:
    - api_token: Your API TOKEN
    - phone_number: Recipient's phone number (639XXXXXXXXX format)
    - message: SMS message content
    
    Optional Parameters:
    - sms_provider: SMS Provider (0, 1, or 2) | default: 2 for multi-network
    
    Returns dict with API response:
    {
        "success": True/False,
        "status": 200,
        "message": "Your SMS message has been successfully added to the queue...",
        "message_id": "iSms-XHYBk",
        "data": {
            "otp_code": "123456",
            "otp_code_expires_at": "...",
            "phone_number": "639171074697"
        }
    }
    """
    print(f"\n{'='*60}")
    print(f"=== iProg Tech SMS API for OTP ===")
    print(f"{'='*60}")
    print(f"Phone number (original): {phone_number}")
    
    if not phone_number:
        print("[ERROR] Missing phone number")
        return {'success': False, 'error': 'Missing phone number'}

    if not SMS_API_TOKEN:
        print("[ERROR] SMS API token not configured")
        return {'success': False, 'error': 'SMS API token not configured'}

    # Format phone number to 639XXXXXXXXX (iProg SMS API format)
    # Remove spaces, dashes, and plus sign
    phone_clean = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    
    # Remove all non-digit characters
    phone_clean = ''.join(filter(str.isdigit, phone_clean))
    
    # Convert to 639XXXXXXXXX format (as shown in API docs)
    if phone_clean.startswith('09'):
        # 09XXXXXXXXX -> 639XXXXXXXXX
        phone_formatted = '63' + phone_clean[1:]
    elif phone_clean.startswith('9') and len(phone_clean) == 10:
        # 9XXXXXXXXX -> 639XXXXXXXXX
        phone_formatted = '63' + phone_clean
    elif phone_clean.startswith('639'):
        # Already in correct format
        phone_formatted = phone_clean
    elif phone_clean.startswith('63') and len(phone_clean) == 12:
        # 63XXXXXXXXXX -> already correct
        phone_formatted = phone_clean
    else:
        # Fallback: try to make it 639 format
        if len(phone_clean) == 10 and phone_clean.startswith('9'):
            phone_formatted = '63' + phone_clean
        else:
            print(f"[ERROR] Invalid phone number format: {phone_number}")
            return {'success': False, 'error': 'Invalid phone number format'}
    
    print(f"Phone number (formatted): {phone_formatted}")

    # Generate OTP code
    otp_code = _generate_otp(6)
    
    # Store OTP for later verification
    _store_otp(phone_formatted, otp_code, expires_in_minutes=5)
    
    # Build OTP message
    if message and ':otp' in message:
        # Replace :otp placeholder with actual code
        otp_message = message.replace(':otp', otp_code)
    else:
        # Default OTP message with E-KOLEK branding
        otp_message = (
            f"Your E-KOLEK verification code is: {otp_code}\n"
            f"This code is valid for 5 minutes.\n"
            f"Do not share this code with anyone.\n"
            f"- E-KOLEK Team"
        )
    
    print(f"[INFO] Generated OTP: {otp_code}")
    print(f"[INFO] OTP Message: {otp_message}")

    # Build payload for SMS API
    payload = {
        'api_token': SMS_API_TOKEN,
        'phone_number': phone_formatted,
        'message': otp_message,
        'sms_provider': SMS_PROVIDER  # Multi-network provider
    }

    print(f"\n[REQUEST] Endpoint: {SMS_API_URL}")
    print(f"[REQUEST] Phone: {phone_formatted}")
    print(f"[REQUEST] SMS Provider: {SMS_PROVIDER}")
    
    result = _post_json(SMS_API_URL, payload)
    
    print(f"\n[RESULT] API Response: {result}")
    
    # Transform SMS API response to match OTP service interface
    if isinstance(result, dict):
        if result.get('success') or result.get('status') == 200:
            # Successfully sent
            from datetime import datetime, timedelta
            expires_at = (datetime.now() + timedelta(minutes=5)).isoformat()
            
            result['success'] = True
            result['data'] = {
                'otp_code': otp_code,  # Include OTP for logging/debugging
                'otp_code_expires_at': expires_at,
                'otp_code_confirmed': False,
                'phone_number': phone_formatted,
                'message': otp_message
            }
            print(f"[SUCCESS] OTP sent successfully!")
            print(f"[OTP] Code: {otp_code}")
            print(f"[OTP] Expires: {expires_at}")
            print(f"[OTP] Phone: {phone_formatted}")
        else:
            result['success'] = False
    
    print(f"[RESULT] Success: {result.get('success', False)}")
    print(f"{'='*60}\n")
    return result




def verify_otp(phone_number, otp_code):
    """
    Verify OTP using local storage (no API call needed)
    
    Since we're using SMS API to send OTPs, we manage verification locally.
    The OTP is stored in memory when sent and verified here.
    
    Phone format: Must match the format used in send_otp (639XXXXXXXXX)
    
    Returns dict with verification result:
    {
        "status": "success",
        "message": "OTP verified successfully"
    }
    """
    print(f"\n{'='*60}")
    print(f"=== OTP SERVICE: verify_otp called ===")
    print(f"{'='*60}")
    print(f"Phone number (original): {phone_number}")
    print(f"OTP code: {otp_code}")
    
    if not phone_number or not otp_code:
        print("[ERROR] Missing phone number or OTP")
        return {'success': False, 'error': 'Missing phone number or otp'}

    # Format phone number to 639XXXXXXXXX (SAME FORMAT AS SEND_OTP)
    # Remove spaces, dashes, and plus sign
    phone_clean = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    
    # Remove all non-digit characters
    phone_clean = ''.join(filter(str.isdigit, phone_clean))
    
    # Convert to 639XXXXXXXXX format (must match send_otp format)
    if phone_clean.startswith('09'):
        # 09XXXXXXXXX -> 639XXXXXXXXX
        phone_formatted = '63' + phone_clean[1:]
    elif phone_clean.startswith('9') and len(phone_clean) == 10:
        # 9XXXXXXXXX -> 639XXXXXXXXX
        phone_formatted = '63' + phone_clean
    elif phone_clean.startswith('639'):
        # Already in correct format
        phone_formatted = phone_clean
    elif phone_clean.startswith('63') and len(phone_clean) == 12:
        # 63XXXXXXXXXX -> already correct
        phone_formatted = phone_clean
    else:
        # Fallback: try to make it 639 format
        if len(phone_clean) == 10 and phone_clean.startswith('9'):
            phone_formatted = '63' + phone_clean
        else:
            phone_formatted = phone_clean
    
    print(f"Phone number (formatted): {phone_formatted}")
    
    # Verify OTP from local storage
    result = _verify_stored_otp(phone_formatted, otp_code)
    
    print(f"\n[RESULT] Verify result: {result}")
    print(f"[RESULT] Success: {result.get('success', False)}")
    print(f"{'='*60}\n")
    return result


def list_otps():
    """
    List stored OTPs (for debugging purposes only)
    Returns list of active OTPs in storage
    """
    from datetime import datetime
    
    active_otps = []
    for phone, data in _otp_storage.items():
        if datetime.now() < data['expires_at']:
            active_otps.append({
                'phone_number': phone,
                'expires_at': data['expires_at'].isoformat(),
                'attempts': data['attempts']
            })
    
    return {
        'success': True,
        'count': len(active_otps),
        'otps': active_otps
    }
