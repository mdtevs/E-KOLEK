import os
import requests
import logging
from django.conf import settings
import random
import string
import json
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Load API token from environment or Django settings
# Using SMS_API_TOKEN for sending OTP via SMS API
SMS_API_TOKEN = os.environ.get('SMS_API_TOKEN') or getattr(settings, 'SMS_API_TOKEN', None)
SMS_PROVIDER = getattr(settings, 'SMS_PROVIDER', 2)  # Default to 2 for multi-network support

# iProg Tech SMS API endpoint for sending OTP
SMS_API_URL = 'https://www.iprogsms.com/api/v1/sms_messages'

# REDIS-BACKED OTP STORAGE (survives server restarts!)
# Using Django's cache framework (configured with Redis on Railway)
# Cache keys: otp_{phone_number}, verified_{phone_number}

# ========================================
# OTP RATE LIMITING CONFIGURATION
# ========================================
# Industry standards for OTP rate limiting:
# - Send limit: 3 requests per hour (prevents spam/abuse)
# - Verification attempts: 5 attempts per OTP
# - Cooldown period: 15 minutes after exceeding limits
# - Max OTP validity: 5 minutes

OTP_SEND_LIMIT = 3  # Max OTP sends per hour
OTP_SEND_WINDOW_MINUTES = 60  # Time window for send limit
OTP_MAX_VERIFY_ATTEMPTS = 5  # Max verification attempts per OTP
OTP_COOLDOWN_MINUTES = 15  # Lockout period after exceeding limits
OTP_EXPIRY_MINUTES = 5  # OTP validity period


def _check_send_rate_limit(phone_number):
    """
    Check if phone number has exceeded OTP send rate limit.
    
    Returns:
        dict: {'allowed': bool, 'error': str, 'retry_after': int}
    """
    send_count_key = f'otp_send_count_{phone_number}'
    cooldown_key = f'otp_cooldown_{phone_number}'
    
    # Check if in cooldown period
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Phone {phone_number} is in cooldown period. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many OTP requests. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            # Cooldown expired, remove it
            cache.delete(cooldown_key)
    
    # Get current send count
    send_data = cache.get(send_count_key)
    if send_data:
        send_info = json.loads(send_data)
        count = send_info.get('count', 0)
        first_send = datetime.fromisoformat(send_info.get('first_send'))
        
        # Check if we're still within the time window
        time_elapsed = datetime.now() - first_send
        if time_elapsed < timedelta(minutes=OTP_SEND_WINDOW_MINUTES):
            if count >= OTP_SEND_LIMIT:
                # Exceeded limit - set cooldown
                cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
                cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)
                
                logger.warning(f"[RATE LIMIT] Phone {phone_number} exceeded send limit ({count}/{OTP_SEND_LIMIT}). Cooldown for {OTP_COOLDOWN_MINUTES}min")
                return {
                    'allowed': False,
                    'error': f'Too many OTP requests. You have reached the limit of {OTP_SEND_LIMIT} requests per hour. Please wait {OTP_COOLDOWN_MINUTES} minutes.',
                    'retry_after': OTP_COOLDOWN_MINUTES * 60
                }
            else:
                # Within limit, increment counter
                send_info['count'] = count + 1
                send_info['last_send'] = datetime.now().isoformat()
                remaining_time = OTP_SEND_WINDOW_MINUTES * 60 - int(time_elapsed.total_seconds())
                cache.set(send_count_key, json.dumps(send_info), timeout=remaining_time)
                logger.info(f"[RATE LIMIT] Phone {phone_number} OTP send count: {count + 1}/{OTP_SEND_LIMIT}")
                return {'allowed': True}
        else:
            # Time window expired, reset counter
            cache.delete(send_count_key)
    
    # First send or counter expired, initialize
    send_info = {
        'count': 1,
        'first_send': datetime.now().isoformat(),
        'last_send': datetime.now().isoformat()
    }
    cache.set(send_count_key, json.dumps(send_info), timeout=OTP_SEND_WINDOW_MINUTES * 60)
    logger.info(f"[RATE LIMIT] Phone {phone_number} OTP send count: 1/{OTP_SEND_LIMIT}")
    return {'allowed': True}


def _check_verify_rate_limit(phone_number):
    """
    Check if phone number has exceeded OTP verification attempt limit.
    
    Returns:
        dict: {'allowed': bool, 'error': str, 'attempts_left': int}
    """
    attempts_key = f'otp_verify_attempts_{phone_number}'
    cooldown_key = f'otp_verify_cooldown_{phone_number}'
    
    # Check if in verification cooldown
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Phone {phone_number} is in verification cooldown. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many failed verification attempts. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            cache.delete(cooldown_key)
    
    # Get current attempt count
    attempt_data = cache.get(attempts_key)
    if attempt_data:
        attempt_info = json.loads(attempt_data)
        count = attempt_info.get('count', 0)
        
        if count >= OTP_MAX_VERIFY_ATTEMPTS:
            # Exceeded limit - set cooldown
            cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
            cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)
            cache.delete(attempts_key)
            
            logger.warning(f"[RATE LIMIT] Phone {phone_number} exceeded verification attempts ({count}/{OTP_MAX_VERIFY_ATTEMPTS}). Cooldown for {OTP_COOLDOWN_MINUTES}min")
            return {
                'allowed': False,
                'error': f'Too many failed attempts. Please wait {OTP_COOLDOWN_MINUTES} minutes before trying again.',
                'retry_after': OTP_COOLDOWN_MINUTES * 60
            }
        
        return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS - count}
    
    return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS}


def _increment_verify_attempts(phone_number):
    """Increment verification attempt counter"""
    attempts_key = f'otp_verify_attempts_{phone_number}'
    attempt_data = cache.get(attempts_key)
    
    if attempt_data:
        attempt_info = json.loads(attempt_data)
        attempt_info['count'] = attempt_info.get('count', 0) + 1
        attempt_info['last_attempt'] = datetime.now().isoformat()
    else:
        attempt_info = {
            'count': 1,
            'first_attempt': datetime.now().isoformat(),
            'last_attempt': datetime.now().isoformat()
        }
    
    # Store for OTP expiry time + 5 minutes buffer
    cache.set(attempts_key, json.dumps(attempt_info), timeout=(OTP_EXPIRY_MINUTES + 5) * 60)
    logger.info(f"[RATE LIMIT] Phone {phone_number} verification attempts: {attempt_info['count']}/{OTP_MAX_VERIFY_ATTEMPTS}")


def _clear_verify_attempts(phone_number):
    """Clear verification attempt counter on successful verification"""
    attempts_key = f'otp_verify_attempts_{phone_number}'
    cache.delete(attempts_key)
    logger.info(f"[RATE LIMIT] Phone {phone_number} verification attempts cleared after successful verification")



def _generate_otp(length=6):
    """Generate a random numeric OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def _store_otp(phone_number, otp_code, expires_in_minutes=None):
    """Store OTP in Redis cache with expiration time"""
    if expires_in_minutes is None:
        expires_in_minutes = OTP_EXPIRY_MINUTES
        
    from datetime import datetime, timedelta
    expiry = datetime.now() + timedelta(minutes=expires_in_minutes)
    
    otp_data = {
        'otp': otp_code,
        'expires_at': expiry.isoformat(),
        'attempts': 0,
        'created_at': datetime.now().isoformat()
    }
    
    # Store in Redis with TTL (Time To Live)
    cache_key = f'otp_{phone_number}'
    cache.set(cache_key, json.dumps(otp_data), timeout=expires_in_minutes * 60)
    
    print(f"[REDIS] Stored OTP for {phone_number} in Redis with {expires_in_minutes}min TTL")
    print(f"[REDIS] Cache key: {cache_key}")


def _verify_stored_otp(phone_number, otp_code):
    """Verify OTP from Redis cache with rate limiting"""
    from datetime import datetime, timedelta
    
    # Check verification rate limit FIRST
    rate_limit = _check_verify_rate_limit(phone_number)
    if not rate_limit['allowed']:
        return {
            'success': False,
            'error': rate_limit['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }
    
    # Check if this OTP was recently verified (within last 2 minutes)
    verified_key = f'verified_{phone_number}'
    recently_verified = cache.get(verified_key)
    
    if recently_verified:
        verified_data = json.loads(recently_verified)
        verified_at = datetime.fromisoformat(verified_data['verified_at'])
        time_since_verify = datetime.now() - verified_at
        if time_since_verify < timedelta(minutes=2):
            print(f"[REDIS] OTP for {phone_number} was recently verified {time_since_verify.seconds}s ago - returning cached success")
            return {'success': True, 'status': 'success', 'message': 'OTP verified successfully', 'already_verified': True}
    
    # Get OTP from Redis
    cache_key = f'otp_{phone_number}'
    stored_json = cache.get(cache_key)
    
    if not stored_json:
        print(f"[REDIS] OTP not found in cache for {phone_number}")
        _increment_verify_attempts(phone_number)
        return {'success': False, 'error': 'OTP not found or expired. Please request a new OTP.', 'error_type': 'otp_not_found'}
    
    stored_data = json.loads(stored_json)
    
    # Check expiration
    expires_at = datetime.fromisoformat(stored_data['expires_at'])
    if datetime.now() > expires_at:
        cache.delete(cache_key)
        print(f"[REDIS] OTP expired for {phone_number}")
        _increment_verify_attempts(phone_number)
        return {'success': False, 'error': 'OTP has expired. Please request a new OTP.', 'error_type': 'otp_expired'}
    
    # Check OTP-specific attempts (legacy support - now using global rate limit)
    if stored_data.get('attempts', 0) >= 3:
        cache.delete(cache_key)
        print(f"[REDIS] Too many attempts for {phone_number}")
        return {'success': False, 'error': 'Too many failed attempts. Please request a new OTP.', 'error_type': 'too_many_attempts'}
    
    # Verify OTP
    if stored_data['otp'] == str(otp_code):
        cache.delete(cache_key)  # Clear OTP after successful verification
        
        # Clear verification attempt counter
        _clear_verify_attempts(phone_number)
        
        # Track this as recently verified (cache for 2 minutes)
        verified_data = {
            'verified_at': datetime.now().isoformat(),
            'otp_code': otp_code
        }
        cache.set(verified_key, json.dumps(verified_data), timeout=120)  # 2 minutes
        
        print(f"[REDIS] ✅ OTP verified successfully for {phone_number}")
        return {'success': True, 'status': 'success', 'message': 'OTP verified successfully'}
    else:
        # Increment both OTP-specific attempts AND global verification attempts
        stored_data['attempts'] += 1
        cache.set(cache_key, json.dumps(stored_data), timeout=300)  # Keep same 5min TTL
        _increment_verify_attempts(phone_number)
        
        attempts_left = rate_limit.get('attempts_left', OTP_MAX_VERIFY_ATTEMPTS) - 1
        print(f"[REDIS] ❌ Invalid OTP for {phone_number}. Attempts remaining: {attempts_left}/{OTP_MAX_VERIFY_ATTEMPTS}")
        
        error_msg = f'Invalid OTP code. {attempts_left} attempts remaining.'
        if attempts_left == 0:
            error_msg = 'Invalid OTP code. No attempts remaining. Please wait before trying again.'
            
        return {
            'success': False,
            'error': error_msg,
            'error_type': 'invalid_otp',
            'attempts_left': attempts_left
        }


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
    Send OTP using iProg Tech SMS API with rate limiting
    
    Rate Limiting (Industry Standards):
    - Maximum 3 OTP sends per hour
    - 15-minute cooldown after exceeding limit
    - Prevents spam and reduces costs
    
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

    # CHECK RATE LIMIT BEFORE SENDING
    rate_limit_check = _check_send_rate_limit(phone_formatted)
    if not rate_limit_check['allowed']:
        print(f"[RATE LIMIT BLOCKED] {rate_limit_check['error']}")
        return {
            'success': False,
            'error': rate_limit_check['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit_check.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }

    # Generate OTP code
    otp_code = _generate_otp(6)
    
    # Store OTP for later verification
    _store_otp(phone_formatted, otp_code, expires_in_minutes=OTP_EXPIRY_MINUTES)
    
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
        'sms_provider': SMS_PROVIDER,  # Multi-network provider
        'sender_name': 'Ka Prets'  # Temporary sender name for all networks (Dec 23, 2025)
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
    List stored OTPs from Redis (for debugging purposes only)
    Returns list of active OTPs in cache
    
    Note: This is a simple implementation. In production with many OTPs,
    consider maintaining a separate index or using Redis SCAN command.
    """
    print("[REDIS] Note: list_otps() requires Redis KEYS command - use cautiously in production")
    return {
        'success': True,
        'message': 'OTP listing disabled - OTPs are stored in Redis with individual keys',
        'count': 0,
        'otps': []
    }
