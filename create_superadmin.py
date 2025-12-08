r"""
CENRO E-Kolek Super Administrator Creation Script

This script creates a Super Administrator account with full system access.
The superadmin will have:
- All permissions enabled (users, points, rewards, schedules, learning, games, security, controls)
- Auto-approved status (bypasses pending approval workflow)
- Access to all barangays in the system
- Audit trail entry for account creation
- Password security validation

Usage:
    python create_superadmin.py

Or with Django's virtual environment:
    env\Scripts\python.exe create_superadmin.py

Author: System Administrator
Date: November 26, 2025
"""

import os
import sys
import django
import getpass
import re
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from cenro.models import AdminUser, AdminActionHistory
from accounts.models import Barangay


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """Print script header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  CENRO E-KOLEK SYSTEM - SUPER ADMINISTRATOR CREATION  {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    print(f"{Colors.OKCYAN}This script will create a Super Administrator account with full system access.{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  Super Admins have unrestricted access to all system functions.{Colors.ENDC}\n")


def validate_username(username):
    """Validate username format"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 100:
        return False, "Username must not exceed 100 characters"
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
    return True, ""


def validate_email(email):
    """Validate email format"""
    if not email:
        return True, ""  # Email is optional
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numbers"
    
    strength = "Medium"
    if has_special and len(password) >= 12:
        strength = "Strong"
    
    return True, f"Password strength: {strength}"


def get_input(prompt, validator=None, allow_empty=False):
    """Get user input with optional validation"""
    while True:
        value = input(f"{Colors.OKBLUE}{prompt}{Colors.ENDC}").strip()
        
        if not value and not allow_empty:
            print(f"{Colors.FAIL}❌ This field is required. Please try again.{Colors.ENDC}")
            continue
        
        if not value and allow_empty:
            return value
        
        if validator:
            is_valid, message = validator(value)
            if not is_valid:
                print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
                continue
            if message:  # Print info message (like password strength)
                print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
        
        return value


def get_password():
    """Get and confirm password securely"""
    while True:
        password = getpass.getpass(f"{Colors.OKBLUE}Enter password: {Colors.ENDC}")
        
        if not password:
            print(f"{Colors.FAIL}❌ Password is required.{Colors.ENDC}")
            continue
        
        is_valid, message = validate_password(password)
        if not is_valid:
            print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
            continue
        
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
        
        confirm = getpass.getpass(f"{Colors.OKBLUE}Confirm password: {Colors.ENDC}")
        
        if password != confirm:
            print(f"{Colors.FAIL}❌ Passwords do not match. Please try again.{Colors.ENDC}")
            continue
        
        return password


def create_superadmin():
    """Main function to create superadmin"""
    print_header()
    
    # Check if any superadmin exists
    existing_superadmins = AdminUser.objects.filter(role='super_admin', is_active=True)
    if existing_superadmins.exists():
        print(f"{Colors.WARNING}⚠️  Existing Super Administrators:{Colors.ENDC}")
        for admin in existing_superadmins:
            status = "🟢 Active" if admin.status == 'approved' else f"🟡 {admin.status.title()}"
            print(f"   • {admin.username} - {admin.full_name} ({status})")
        print()
        
        proceed = input(f"{Colors.WARNING}Create another superadmin? (yes/no): {Colors.ENDC}").strip().lower()
        if proceed not in ['yes', 'y']:
            print(f"\n{Colors.OKCYAN}Operation cancelled.{Colors.ENDC}")
            return
        print()
    
    # Get superadmin details
    print(f"{Colors.BOLD}Step 1: Basic Information{Colors.ENDC}")
    print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    
    # Username
    while True:
        username = get_input("Username: ", validate_username)
        if AdminUser.objects.filter(username=username).exists():
            print(f"{Colors.FAIL}❌ Username '{username}' already exists. Choose another.{Colors.ENDC}")
            continue
        break
    
    # Full name
    full_name = get_input("Full name: ")
    
    # Email (optional)
    email = get_input("Email (optional, press Enter to skip): ", validate_email, allow_empty=True)
    if not email:
        email = None
    
    print()
    print(f"{Colors.BOLD}Step 2: Security{Colors.ENDC}")
    print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    print(f"{Colors.WARNING}Password requirements:{Colors.ENDC}")
    print(f"  • Minimum 8 characters")
    print(f"  • Must contain uppercase and lowercase letters")
    print(f"  • Must contain numbers")
    print(f"  • Special characters recommended (!@#$%^&*()_+-=[]{{}}|;:,.<>?)")
    print()
    
    password = get_password()
    
    print()
    print(f"{Colors.BOLD}Step 3: Barangay Assignment{Colors.ENDC}")
    print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    
    # Get all barangays
    all_barangays = Barangay.objects.all().order_by('name')
    barangay_count = all_barangays.count()
    
    if barangay_count > 0:
        print(f"{Colors.OKGREEN}Found {barangay_count} barangay(s) in the system:{Colors.ENDC}")
        for idx, barangay in enumerate(all_barangays, 1):
            print(f"  {idx}. {barangay.name}")
        print()
        
        assign_all = input(f"{Colors.OKBLUE}Assign all barangays to this superadmin? (yes/no, default: yes): {Colors.ENDC}").strip().lower()
        assign_barangays = assign_all in ['', 'yes', 'y']
    else:
        print(f"{Colors.WARNING}⚠️  No barangays found in the system.{Colors.ENDC}")
        print(f"{Colors.OKCYAN}   You can add barangays later through the admin panel.{Colors.ENDC}")
        assign_barangays = False
    
    print()
    print(f"{Colors.BOLD}Step 4: Confirmation{Colors.ENDC}")
    print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    print(f"{Colors.BOLD}Please review the information:{Colors.ENDC}\n")
    print(f"  Username:       {Colors.OKGREEN}{username}{Colors.ENDC}")
    print(f"  Full Name:      {Colors.OKGREEN}{full_name}{Colors.ENDC}")
    print(f"  Email:          {Colors.OKGREEN}{email or '(not provided)'}{Colors.ENDC}")
    print(f"  Role:           {Colors.OKGREEN}Super Administrator{Colors.ENDC}")
    print(f"  Status:         {Colors.OKGREEN}Auto-approved (Active){Colors.ENDC}")
    
    if assign_barangays and barangay_count > 0:
        print(f"  Barangays:      {Colors.OKGREEN}All {barangay_count} barangay(s){Colors.ENDC}")
    else:
        print(f"  Barangays:      {Colors.WARNING}None (can be assigned later){Colors.ENDC}")
    
    print(f"\n  {Colors.BOLD}Permissions:{Colors.ENDC}")
    permissions = [
        "✓ Manage Users",
        "✓ Manage Controls", 
        "✓ Manage Points",
        "✓ Manage Rewards",
        "✓ Manage Schedules",
        "✓ Manage Security",
        "✓ Manage Learning Content",
        "✓ Manage Games",
        "✓ View All (Full System Access)"
    ]
    for perm in permissions:
        print(f"    {Colors.OKGREEN}{perm}{Colors.ENDC}")
    
    print()
    confirm = input(f"{Colors.BOLD}Create this superadmin account? (yes/no): {Colors.ENDC}").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print(f"\n{Colors.WARNING}❌ Operation cancelled. No account was created.{Colors.ENDC}")
        return
    
    print()
    print(f"{Colors.OKCYAN}Creating superadmin account...{Colors.ENDC}")
    
    try:
        with transaction.atomic():
            # Create superadmin
            superadmin = AdminUser(
                username=username,
                full_name=full_name,
                email=email,
                role='super_admin',
                status='approved',  # Auto-approve superadmin
                approval_date=timezone.now(),
                is_active=True
            )
            
            # Set password
            superadmin.set_password(password)
            
            # Save (this will trigger the save() method which sets all permissions)
            superadmin.save()
            
            # Assign barangays if requested
            if assign_barangays and barangay_count > 0:
                superadmin.assigned_barangays.set(all_barangays)
                print(f"{Colors.OKGREEN}✓ Assigned {barangay_count} barangay(s){Colors.ENDC}")
            
            # Create audit trail entry
            try:
                audit_entry = AdminActionHistory(
                    admin_user=superadmin,
                    target_admin=superadmin,
                    action='create_admin',
                    description=f"Super Administrator account created via creation script",
                    details={
                        'role': 'super_admin',
                        'created_by': 'system_script',
                        'auto_approved': True,
                        'barangays_assigned': barangay_count if assign_barangays else 0,
                        'timestamp': timezone.now().isoformat()
                    },
                    ip_address='127.0.0.1',
                    user_agent='CreateSuperAdmin Script v1.0'
                )
                audit_entry.save()
                print(f"{Colors.OKGREEN}✓ Audit trail entry created{Colors.ENDC}")
            except Exception as audit_error:
                print(f"{Colors.WARNING}⚠️  Could not create audit entry: {audit_error}{Colors.ENDC}")
            
            # Success message
            print()
            print(f"{Colors.OKGREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{Colors.BOLD}  ✅ SUPERADMIN ACCOUNT CREATED SUCCESSFULLY!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
            
            print(f"{Colors.BOLD}Account Details:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            print(f"  👤 Username:    {Colors.OKGREEN}{superadmin.username}{Colors.ENDC}")
            print(f"  📛 Full Name:   {Colors.OKGREEN}{superadmin.full_name}{Colors.ENDC}")
            print(f"  📧 Email:       {Colors.OKGREEN}{superadmin.email or '(not provided)'}{Colors.ENDC}")
            print(f"  🎭 Role:        {Colors.OKGREEN}{superadmin.get_role_display()}{Colors.ENDC}")
            print(f"  ✅ Status:      {Colors.OKGREEN}{superadmin.get_status_display()}{Colors.ENDC}")
            print(f"  🆔 Admin ID:    {Colors.OKGREEN}{superadmin.id}{Colors.ENDC}")
            print(f"  📅 Created:     {Colors.OKGREEN}{superadmin.created_at.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
            
            print()
            print(f"{Colors.BOLD}System Access:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            print(f"  🌐 Admin Portal:  {Colors.OKGREEN}/cenro/admin/login/{Colors.ENDC}")
            print(f"  🔐 Login with:    {Colors.OKGREEN}{username}{Colors.ENDC}")
            
            print()
            print(f"{Colors.BOLD}Permissions Granted:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            
            permission_checks = [
                ('can_manage_users', '👥 Manage Users'),
                ('can_manage_controls', '⚙️  Manage Controls'),
                ('can_manage_points', '💰 Manage Points'),
                ('can_manage_rewards', '🎁 Manage Rewards'),
                ('can_manage_schedules', '📅 Manage Schedules'),
                ('can_manage_security', '🔒 Manage Security'),
                ('can_manage_learning', '📚 Manage Learning'),
                ('can_manage_games', '🎮 Manage Games'),
                ('can_view_all', '👁️  View All Sections'),
            ]
            
            for attr, label in permission_checks:
                if hasattr(superadmin, attr) and getattr(superadmin, attr):
                    print(f"  {Colors.OKGREEN}✓ {label}{Colors.ENDC}")
            
            if assign_barangays and barangay_count > 0:
                print()
                print(f"{Colors.BOLD}Barangay Management:{Colors.ENDC}")
                print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
                print(f"  {Colors.OKGREEN}✓ Access to all {barangay_count} barangay(s){Colors.ENDC}")
            
            print()
            print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            print(f"  1. Start the server:  {Colors.OKGREEN}env\\Scripts\\python.exe manage.py runserver{Colors.ENDC}")
            print(f"  2. Open browser:      {Colors.OKGREEN}http://localhost:8000/cenro/admin/login/{Colors.ENDC}")
            print(f"  3. Login with:        {Colors.OKGREEN}{username}{Colors.ENDC}")
            print(f"  4. Start managing the E-Kolek system!")
            
            print()
            print(f"{Colors.WARNING}⚠️  SECURITY REMINDERS:{Colors.ENDC}")
            print(f"  • Keep your superadmin credentials secure")
            print(f"  • Change password regularly")
            print(f"  • Monitor admin activity logs")
            print(f"  • Don't share superadmin access")
            
            print()
            
    except Exception as e:
        print()
        print(f"{Colors.FAIL}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}  ❌ ERROR CREATING SUPERADMIN{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        print(f"{Colors.FAIL}Error details: {str(e)}{Colors.ENDC}")
        print()
        print(f"{Colors.WARNING}Troubleshooting:{Colors.ENDC}")
        print(f"  • Make sure database is running and migrations are applied")
        print(f"  • Check that Django settings are correct")
        print(f"  • Verify all required models exist (AdminUser, AdminActionHistory, Barangay)")
        print(f"  • Run: {Colors.OKGREEN}env\\Scripts\\python.exe manage.py migrate{Colors.ENDC}")
        print()
        sys.exit(1)


if __name__ == '__main__':
    try:
        create_superadmin()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}❌ Operation cancelled by user.{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Unexpected error: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)
