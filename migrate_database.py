"""
Database Migration Script for E-KOLEK
Migrates from cenro_db to ekolek_cenro
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the new ekolek_cenro database"""
    print("=" * 80)
    print("E-KOLEK Database Migration")
    print("=" * 80)
    print("\nStep 1: Creating new database 'ekolek_cenro'...")
    
    # Database connection parameters
    db_user = 'postgres'
    db_password = 'renz123'
    db_host = 'localhost'
    db_port = '5432'
    new_db_name = 'ekolek_cenro'
    
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (new_db_name,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"✓ Database '{new_db_name}' already exists")
            response = input("Do you want to drop and recreate it? (yes/no): ").strip().lower()
            if response == 'yes':
                print(f"Dropping existing database '{new_db_name}'...")
                cursor.execute(sql.SQL("DROP DATABASE {}").format(
                    sql.Identifier(new_db_name)
                ))
                print("✓ Database dropped")
            else:
                print("Keeping existing database. Proceeding to migrations...")
                cursor.close()
                conn.close()
                return True
        
        if not exists or response == 'yes':
            # Create new database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(new_db_name)
            ))
            print(f"✓ Database '{new_db_name}' created successfully!")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error: {e}")
        return False

def run_migrations():
    """Run Django migrations on the new database"""
    print("\nStep 2: Running Django migrations...")
    print("-" * 80)
    
    # Run migrations
    exit_code = os.system('newenv\\Scripts\\python.exe manage.py migrate')
    
    if exit_code == 0:
        print("✓ Migrations completed successfully!")
        return True
    else:
        print("✗ Migration failed!")
        return False

def main():
    print("\n" + "=" * 80)
    print("IMPORTANT: Make sure you have updated .env file with:")
    print("  DB_NAME=ekolek_cenro")
    print("=" * 80)
    
    response = input("\nHave you updated the .env file? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\nPlease update the .env file first:")
        print("  1. Open .env file")
        print("  2. Change DB_NAME=cenro_db to DB_NAME=ekolek_cenro")
        print("  3. Save the file")
        print("  4. Run this script again")
        return
    
    # Step 1: Create database
    if not create_database():
        print("\n✗ Database creation failed. Please check your PostgreSQL configuration.")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        print("\n✗ Migration failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ Migration Completed Successfully!")
    print("=" * 80)
    print("\nNew database 'ekolek_cenro' is ready to use.")
    print("\nNext steps:")
    print("  1. Create a superadmin: newenv\\Scripts\\python.exe manage.py createsuperuser")
    print("  2. Or use: create_superadmin.bat")
    print("  3. Start the server: start_all.bat")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
