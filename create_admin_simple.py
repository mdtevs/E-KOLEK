#!/usr/bin/env python
"""
Simple script to create CENRO superadmin via Railway
Usage: railway run python create_admin_simple.py
"""
from cenro.models import AdminUser
from accounts.models import Barangay
from django.contrib.auth.hashers import make_password
import sys

# Configuration - EDIT THESE VALUES
USERNAME = 'superadmin'
EMAIL = 'admin@ekolek.com'
PASSWORD = 'Admin@123456'  # CHANGE THIS!
FULL_NAME = 'Super Administrator'

print("=" * 60)
print("CENRO E-KOLEK Superadmin Creation")
print("=" * 60)

# Check if admin already exists
if AdminUser.objects.filter(username=USERNAME).exists():
    print(f"❌ Admin user '{USERNAME}' already exists!")
    existing = AdminUser.objects.get(username=USERNAME)
    print(f"   Email: {existing.email}")
    print(f"   Created: {existing.created_at}")
    sys.exit(1)

# Create superadmin
try:
    admin = AdminUser.objects.create(
        username=USERNAME,
        email=EMAIL,
        password=make_password(PASSWORD),
        full_name=FULL_NAME,
        role='super_admin',
        is_active=True,
        # All permissions enabled
        can_manage_users=True,
        can_manage_points=True,
        can_manage_rewards=True,
        can_manage_schedules=True,
        can_manage_learning=True,
        can_manage_games=True,
        can_manage_security=True,
        can_manage_controls=True,
    )
    
    # Assign all barangays
    all_barangays = Barangay.objects.all()
    barangay_count = all_barangays.count()
    
    if barangay_count > 0:
        admin.barangays.set(all_barangays)
        print(f"✅ Assigned {barangay_count} barangays to admin")
    else:
        print("⚠️  No barangays found in database")
    
    print("\n" + "=" * 60)
    print("✅ SUPERADMIN CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Username:  {admin.username}")
    print(f"Email:     {admin.email}")
    print(f"Full Name: {admin.full_name}")
    print(f"Role:      {admin.role}")
    print(f"Barangays: {admin.barangays.count()}")
    print("\n🔐 Login at: https://e-kolek-production.up.railway.app/cenro/admin/login/")
    print(f"   Username: {USERNAME}")
    print(f"   Password: {PASSWORD}")
    print("\n⚠️  IMPORTANT: Change your password after first login!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error creating admin: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
