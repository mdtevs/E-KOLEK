"""
Validation API views for registration
"""

from django.http import JsonResponse
import re

from accounts.models import Users, Family


def check_phone_availability(request):
    """
    AJAX endpoint to check if a phone number is available for registration.
    Returns JSON with availability status.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        if not phone:
            return JsonResponse({
                'success': False, 
                'error': 'Phone number is required'
            }, status=400)
        
        # Normalize phone number (same format as in forms.py)
        phone_normalized = phone.replace(' ', '').replace('-', '')
        if phone_normalized.startswith('09'):
            phone_normalized = '+63' + phone_normalized[1:]
        elif phone_normalized.startswith('9') and len(phone_normalized) == 10:
            phone_normalized = '+63' + phone_normalized
        elif not phone_normalized.startswith('+'):
            phone_normalized = '+63' + phone_normalized
        
        # Check if phone is already registered (check both formats)
        # Exclude rejected users/families (they should be deleted, but this is a safety check)
        phone_exists = (
            Users.objects.filter(phone=phone).exclude(status='rejected').exists() or
            Users.objects.filter(phone=phone_normalized).exclude(status='rejected').exists() or
            Family.objects.filter(representative_phone=phone).exclude(status='rejected').exists() or
            Family.objects.filter(representative_phone=phone_normalized).exclude(status='rejected').exists()
        )
        
        if phone_exists:
            return JsonResponse({
                'success': False,
                'available': False,
                'message': 'This phone number is already registered. Please use a different number or login if you already have an account.'
            })
        
        return JsonResponse({
            'success': True,
            'available': True,
            'message': 'Phone number is available'
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def check_email_availability(request):
    """
    AJAX endpoint to check if an email address is available for registration.
    Returns JSON with availability status.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required'
            }, status=400)
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return JsonResponse({
                'success': False,
                'available': False,
                'message': 'Please enter a valid email address'
            })
        
        # Check if email is already registered
        email_exists = Users.objects.filter(email__iexact=email).exists()
        
        if email_exists:
            return JsonResponse({
                'success': False,
                'available': False,
                'message': 'This email address is already registered. Please use a different email or login if you already have an account.'
            })
        
        return JsonResponse({
            'success': True,
            'available': True,
            'message': 'Email address is available'
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def get_active_terms(request):
    """
    Public API endpoint to get active Terms and Conditions for registration pages
    Returns both English and Tagalog versions
    """
    from cenro.models import TermsAndConditions
    
    try:
        terms_data = {}
        
        # Get active English terms
        english_terms = TermsAndConditions.get_active_terms('english')
        if english_terms:
            terms_data['english'] = {
                'id': str(english_terms.id),
                'title': english_terms.title,
                'version': english_terms.version,
                'content': english_terms.content,
                'file_url': english_terms.file.url if english_terms.file else None,
                'updated_at': english_terms.updated_at.isoformat()
            }
        else:
            terms_data['english'] = None
        
        # Get active Tagalog terms
        tagalog_terms = TermsAndConditions.get_active_terms('tagalog')
        if tagalog_terms:
            terms_data['tagalog'] = {
                'id': str(tagalog_terms.id),
                'title': tagalog_terms.title,
                'version': tagalog_terms.version,
                'content': tagalog_terms.content,
                'file_url': tagalog_terms.file.url if tagalog_terms.file else None,
                'updated_at': tagalog_terms.updated_at.isoformat()
            }
        else:
            terms_data['tagalog'] = None
        
        return JsonResponse({
            'success': True,
            'terms': terms_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
