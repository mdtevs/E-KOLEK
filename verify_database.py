"""
Database Verification Script
Verifies the ekolek_cenro database migration
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
django.setup()

from django.db import connection
from accounts.models import Barangay, Family, Users, WasteType
from cenro.models import AdminUser

def verify_database():
    """Verify database connection and basic structure"""
    print("=" * 80)
    print("DATABASE MIGRATION VERIFICATION")
    print("=" * 80)
    
    # Get database info
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(), version()')
        db_name, pg_version = cursor.fetchone()
        print(f"\nConnected to: {db_name}")
        print(f"PostgreSQL: {pg_version.split(',')[0]}")
        
        # Count tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        print(f"Total tables: {table_count}")
    
    print("\n" + "-" * 80)
    print("CHECKING CORE MODELS")
    print("-" * 80)
    
    # Check if models are accessible
    models_to_check = [
        ('Barangay', Barangay),
        ('Family', Family),
        ('Users', Users),
        ('WasteType', WasteType),
        ('AdminUser', AdminUser),
    ]
    
    for model_name, model in models_to_check:
        try:
            count = model.objects.count()
            print(f"[OK] {model_name:20} - {count} records")
        except Exception as e:
            print(f"[ERROR] {model_name:20} - {str(e)[:50]}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Create admin user: create_superadmin.bat")
    print("  2. Start the server: start_all.bat")
    print("  3. Access admin panel: http://localhost:8000/cenro/admin/login/")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        verify_database()
    except Exception as e:
        print(f"\nError during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
