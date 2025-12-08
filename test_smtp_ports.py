"""
SMTP Connection Tester for Railway
Tests multiple SMTP configurations to find what works
"""

import socket
import smtplib
import ssl
from email.mime.text import MIMEText
import sys

print("\n" + "="*70)
print("RAILWAY SMTP CONNECTION TESTER")
print("="*70 + "\n")

# Test configurations
configs = [
    # Gmail standard ports
    {"name": "Gmail Port 587 (TLS/STARTTLS)", "host": "smtp.gmail.com", "port": 587, "use_ssl": False, "use_tls": True},
    {"name": "Gmail Port 465 (SSL)", "host": "smtp.gmail.com", "port": 465, "use_ssl": True, "use_tls": False},
    {"name": "Gmail Port 25 (Plain)", "host": "smtp.gmail.com", "port": 25, "use_ssl": False, "use_tls": False},
    
    # Alternative ports (some providers allow these)
    {"name": "Gmail Port 2525 (Alternative)", "host": "smtp.gmail.com", "port": 2525, "use_ssl": False, "use_tls": True},
    {"name": "Gmail Port 8025 (Alternative)", "host": "smtp.gmail.com", "port": 8025, "use_ssl": False, "use_tls": True},
    
    # Try with explicit IPv4
    {"name": "Gmail IPv4 Port 587", "host": "smtp.gmail.com", "port": 587, "use_ssl": False, "use_tls": True, "force_ipv4": True},
    {"name": "Gmail IPv4 Port 465", "host": "smtp.gmail.com", "port": 465, "use_ssl": True, "use_tls": False, "force_ipv4": True},
]

def test_tcp_connection(host, port, timeout=5):
    """Test basic TCP connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_smtp_connection(config):
    """Test SMTP connection with given config"""
    host = config['host']
    port = config['port']
    use_ssl = config['use_ssl']
    use_tls = config['use_tls']
    
    print(f"\n{'─'*70}")
    print(f"Testing: {config['name']}")
    print(f"Host: {host}:{port} | SSL: {use_ssl} | TLS: {use_tls}")
    print(f"{'─'*70}")
    
    # Step 1: Test TCP connection
    print("  [1/3] Testing TCP connection...", end=" ")
    if test_tcp_connection(host, port):
        print("✅ TCP connection successful")
    else:
        print("❌ TCP connection FAILED (Port blocked)")
        return False
    
    # Step 2: Test SMTP handshake
    print("  [2/3] Testing SMTP handshake...", end=" ")
    try:
        if use_ssl:
            # SSL connection (port 465)
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
        else:
            # TLS connection (port 587) or plain
            server = smtplib.SMTP(host, port, timeout=10)
            
            if use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()
        
        print("✅ SMTP handshake successful")
        
        # Step 3: Test authentication (if credentials available)
        print("  [3/3] Testing authentication...", end=" ")
        
        # Try to login (will fail without credentials but shows SMTP is working)
        try:
            import os
            user = os.environ.get('EMAIL_HOST_USER', '')
            password = os.environ.get('EMAIL_HOST_PASSWORD', '')
            
            if user and password:
                server.login(user, password)
                print("✅ Authentication successful")
                server.quit()
                
                print(f"\n{'🎉'*35}")
                print(f"  ✅✅✅ THIS CONFIGURATION WORKS! ✅✅✅")
                print(f"{'🎉'*35}")
                print(f"\nUse these Railway variables:")
                print(f"  EMAIL_HOST = {host}")
                print(f"  EMAIL_PORT = {port}")
                print(f"  EMAIL_USE_SSL = {use_ssl}")
                print(f"  EMAIL_USE_TLS = {use_tls}")
                return True
            else:
                print("⚠️  No credentials (set EMAIL_HOST_USER/PASSWORD to test)")
                server.quit()
                print(f"\n  ✅ SMTP works but needs credentials to verify fully")
                return True
                
        except smtplib.SMTPAuthenticationError:
            print("❌ Authentication failed (but SMTP connection works!)")
            server.quit()
            return True  # Connection works, just wrong credentials
        except Exception as auth_error:
            print(f"❌ Auth error: {str(auth_error)}")
            server.quit()
            return False
            
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ Socket error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ SMTP error: {str(e)}")
        return False

# Run tests
print("Starting SMTP connection tests...")
print("This will test multiple ports to find which ones Railway allows.\n")

working_configs = []

for config in configs:
    if test_smtp_connection(config):
        working_configs.append(config)

# Summary
print("\n" + "="*70)
print("TEST RESULTS SUMMARY")
print("="*70)

if working_configs:
    print(f"\n✅ Found {len(working_configs)} working configuration(s):\n")
    for i, config in enumerate(working_configs, 1):
        print(f"{i}. {config['name']}")
        print(f"   EMAIL_HOST = {config['host']}")
        print(f"   EMAIL_PORT = {config['port']}")
        print(f"   EMAIL_USE_SSL = {config['use_ssl']}")
        print(f"   EMAIL_USE_TLS = {config['use_tls']}")
        print()
else:
    print("\n❌ No working SMTP configurations found.")
    print("\nPossible reasons:")
    print("  1. Railway blocks all outbound SMTP ports")
    print("  2. Firewall rules prevent SMTP connections")
    print("  3. Network policy restricts email sending")
    print("\nRecommendations:")
    print("  1. Contact Railway support to enable SMTP")
    print("  2. Use Railway's SMTP relay service (if available)")
    print("  3. Use SendGrid/Mailgun free tier (alternative)")

print("\n" + "="*70)
