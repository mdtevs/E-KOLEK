# ==================================================
# Production Code Cleanup Script
# ==================================================
# Removes debug print statements and replaces with proper logging
# Run this BEFORE deploying to production

import re
import os
from pathlib import Path

def clean_debug_prints(file_path):
    """Remove debug print statements from a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Pattern 1: print(f"DEBUG: ...")
    pattern1 = r'print\(f"DEBUG: (.+?)"\)'
    content, count1 = re.subn(pattern1, r'logger.debug(f"\1")', content)
    changes_made += count1
    
    # Pattern 2: print(f"✅ ...")
    pattern2 = r'print\(f"✅ (.+?)"\)'
    content, count2 = re.subn(pattern2, r'logger.info(f"\1")', content)
    changes_made += count2
    
    # Pattern 3: print(f"⚠️ ...")
    pattern3 = r'print\(f"⚠️ (.+?)"\)'
    content, count3 = re.subn(pattern3, r'logger.warning(f"\1")', content)
    changes_made += count3
    
    # Pattern 4: print("DEBUG: ...")
    pattern4 = r'print\("DEBUG: (.+?)"\)'
    content, count4 = re.subn(pattern4, r'logger.debug("\1")', content)
    changes_made += count4
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return 0

def main():
    print("=" * 60)
    print("PRODUCTION CODE CLEANUP")
    print("=" * 60)
    print()
    
    # Target directories
    target_dirs = [
        'cenro/views',
        'accounts/views',
        'mobilelogin',
        'game',
        'learn'
    ]
    
    total_files = 0
    total_changes = 0
    
    for dir_path in target_dirs:
        if not os.path.exists(dir_path):
            continue
            
        print(f"Cleaning {dir_path}/...")
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    changes = clean_debug_prints(file_path)
                    
                    if changes > 0:
                        total_files += 1
                        total_changes += changes
                        print(f"  ✓ {file_path}: {changes} changes")
    
    print()
    print("=" * 60)
    print(f"CLEANUP COMPLETE")
    print(f"Files modified: {total_files}")
    print(f"Total changes: {total_changes}")
    print("=" * 60)
    
    if total_changes > 0:
        print()
        print("⚠️  IMPORTANT:")
        print("1. Review the changes with: git diff")
        print("2. Test the application thoroughly")
        print("3. Commit changes: git commit -am 'Remove debug prints, use proper logging'")

if __name__ == '__main__':
    main()
