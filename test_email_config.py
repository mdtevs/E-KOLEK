"""
Test Email Configuration
This script will be deployed to Railway to verify what settings Django is actually loading
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
django.setup()

from django.conf import settings

print("\n" + "="*60)
print("EMAIL CONFIGURATION TEST")
print("="*60 + "\n")

print("🔍 Checking environment variables:")
print(f"   EMAIL_PORT (env): {os.environ.get('EMAIL_PORT', 'NOT SET')}")
print(f"   EMAIL_USE_TLS (env): {os.environ.get('EMAIL_USE_TLS', 'NOT SET')}")
print(f"   EMAIL_USE_SSL (env): {os.environ.get('EMAIL_USE_SSL', 'NOT SET')}")
print()

print("🔍 Checking Django settings:")
print(f"   settings.EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   settings.EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   settings.EMAIL_PORT: {settings.EMAIL_PORT} (type: {type(settings.EMAIL_PORT).__name__})")
print(f"   settings.EMAIL_USE_TLS: {settings.EMAIL_USE_TLS} (type: {type(settings.EMAIL_USE_TLS).__name__})")
print(f"   settings.EMAIL_USE_SSL: {settings.EMAIL_USE_SSL} (type: {type(settings.EMAIL_USE_SSL).__name__})")
print(f"   settings.EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   settings.EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"   settings.EMAIL_TIMEOUT: {settings.EMAIL_TIMEOUT}")
print()

print("✅ Expected configuration for Railway (port 465 SSL):")
print("   EMAIL_PORT = 465")
print("   EMAIL_USE_TLS = False")
print("   EMAIL_USE_SSL = True")
print()

# Check if configuration is correct
is_correct = (
    settings.EMAIL_PORT == 465 and
    settings.EMAIL_USE_TLS == False and
    settings.EMAIL_USE_SSL == True
)

if is_correct:
    print("✅ Configuration is CORRECT for Railway!")
else:
    print("❌ Configuration is INCORRECT!")
    print("\n🔧 Issues detected:")
    if settings.EMAIL_PORT != 465:
        print(f"   ❌ EMAIL_PORT is {settings.EMAIL_PORT}, should be 465")
    if settings.EMAIL_USE_TLS != False:
        print(f"   ❌ EMAIL_USE_TLS is {settings.EMAIL_USE_TLS}, should be False")
    if settings.EMAIL_USE_SSL != True:
        print(f"   ❌ EMAIL_USE_SSL is {settings.EMAIL_USE_SSL}, should be True")

print("\n" + "="*60)

# Test actual SMTP connection
print("\n🔌 Testing SMTP connection...")
try:
    from django.core.mail import EmailMessage
    
    # Create test email but don't send
    email = EmailMessage(
        subject='Test Email Configuration',
        body='This is a test email to verify SMTP settings.',
        from_email=settings.EMAIL_HOST_USER,
        to=['test@example.com']
    )
    
    # Get the connection
    connection = email.get_connection()
    
    print(f"   Backend: {connection.__class__.__name__}")
    print(f"   Host: {connection.host}")
    print(f"   Port: {connection.port}")
    print(f"   Use TLS: {connection.use_tls}")
    print(f"   Use SSL: {connection.use_ssl}")
    print(f"   Timeout: {connection.timeout}")
    
    # Try to open connection
    print("\n🔌 Attempting to connect to SMTP server...")
    connection.open()
    print("✅ SMTP connection successful!")
    connection.close()
    print("✅ SMTP connection closed cleanly")
    
except Exception as e:
    print(f"❌ SMTP connection failed: {str(e)}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())

print("\n" + "="*60)
