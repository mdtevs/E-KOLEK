"""
Railway SMTP Connection Debugger
Diagnoses why Gmail SMTP isn't working and tests network connectivity
"""

import socket
import smtplib
import ssl
import os
import sys

def test_dns_resolution(host):
    """Test if we can resolve the hostname"""
    print(f"\n[1/5] Testing DNS resolution for {host}...")
    try:
        ip = socket.gethostbyname(host)
        print(f"✅ DNS resolved: {host} -> {ip}")
        return True, ip
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {str(e)}")
        return False, None

def test_tcp_connection(host, port, timeout=10):
    """Test raw TCP connection to SMTP server"""
    print(f"\n[2/5] Testing TCP connection to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP connection successful on port {port}")
            return True
        else:
            print(f"❌ TCP connection failed on port {port} (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ TCP connection error: {str(e)}")
        return False

def test_smtp_handshake(host, port, use_ssl=False, use_tls=False):
    """Test SMTP protocol handshake"""
    print(f"\n[3/5] Testing SMTP handshake ({host}:{port}, SSL={use_ssl}, TLS={use_tls})...")
    try:
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()
        
        # Get server response
        code, msg = server.noop()
        print(f"✅ SMTP handshake successful (code {code})")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP handshake failed: {str(e)}")
        return False

def test_smtp_auth(host, port, user, password, use_ssl=False, use_tls=False):
    """Test SMTP authentication"""
    print(f"\n[4/5] Testing SMTP authentication...")
    
    if not user or not password:
        print("⚠️  No credentials provided (set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)")
        return False
    
    try:
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()
        
        server.login(user, password)
        print(f"✅ SMTP authentication successful")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("   Check: EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False

def test_network_policies():
    """Test for common network restrictions"""
    print(f"\n[5/5] Testing network environment...")
    
    # Check if we're in Railway
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
    if railway_env:
        print(f"✅ Running in Railway environment: {railway_env}")
    else:
        print("⚠️  Not running in Railway (local environment)")
    
    # Check outbound connectivity to well-known services
    print("\nTesting outbound connectivity:")
    
    # Test HTTPS (should always work)
    try:
        import urllib.request
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("  ✅ HTTPS (443) - Working")
    except:
        print("  ❌ HTTPS (443) - Blocked")
    
    # Test common ports
    test_ports = [
        (25, "SMTP"),
        (587, "SMTP TLS"),
        (465, "SMTP SSL"),
        (2525, "Alternative SMTP")
    ]
    
    for port, name in test_ports:
        if test_tcp_connection('smtp.gmail.com', port, timeout=3):
            print(f"  ✅ Port {port} ({name}) - OPEN")
        else:
            print(f"  ❌ Port {port} ({name}) - BLOCKED")

def main():
    print("="*70)
    print("RAILWAY SMTP CONNECTION DEBUGGER")
    print("="*70)
    
    # Configuration
    host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('EMAIL_PORT', 587))
    user = os.environ.get('EMAIL_HOST_USER', '')
    password = os.environ.get('EMAIL_HOST_PASSWORD', '')
    use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
    
    print(f"\nConfiguration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user if user else '(not set)'}")
    print(f"  Password: {'*' * len(password) if password else '(not set)'}")
    print(f"  TLS: {use_tls}")
    print(f"  SSL: {use_ssl}")
    
    # Run all tests
    dns_ok, ip = test_dns_resolution(host)
    
    if dns_ok:
        tcp_ok = test_tcp_connection(host, port)
        
        if tcp_ok:
            smtp_ok = test_smtp_handshake(host, port, use_ssl, use_tls)
            
            if smtp_ok:
                auth_ok = test_smtp_auth(host, port, user, password, use_ssl, use_tls)
                
                if auth_ok:
                    print("\n" + "="*70)
                    print("🎉 ALL TESTS PASSED! SMTP SHOULD WORK!")
                    print("="*70)
                    return 0
    
    # Check for specific issues
    print("\n" + "="*70)
    print("❌ SMTP CONNECTION FAILED")
    print("="*70)
    
    test_network_policies()
    
    print("\n💡 NEXT STEPS:")
    print("1. If all ports are BLOCKED → Contact Railway support")
    print("2. If authentication failed → Check EMAIL_HOST_PASSWORD")
    print("3. If DNS failed → Check EMAIL_HOST setting")
    print("4. Try running this from Railway CLI: railway run python debug_smtp.py")
    print("="*70)
    
    return 1

if __name__ == '__main__':
    sys.exit(main())
