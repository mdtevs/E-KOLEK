"""
Utility functions for CENRO views
"""
import qrcode
import io
import base64
from django.utils import timezone


def generate_qr_code_base64(data):
    """Generate QR code as base64 encoded string"""
    qr = qrcode.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"


def get_time_ago(dt):
    """Helper function to convert datetime to 'time ago' format"""
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"
