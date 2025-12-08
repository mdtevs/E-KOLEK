"""
Code Quality Cleanup Script
Automatically fixes common code quality issues across the codebase
"""
import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Apps to clean
APPS = ['accounts', 'cenro', 'game', 'learn', 'mobilelogin', 'ekoscan']

# Cleanup statistics
stats = {
    'files_processed': 0,
    'empty_except_pass_fixed': 0,
    'comments_cleaned': 0,
    'imports_organized': 0
}


def clean_empty_except_pass(content):
    """Remove empty except: pass blocks that don't add value"""
    # Pattern: except SomeException:
    #              pass
    # This is often used unnecessarily
    changes = 0
    
    # Count occurrences before cleanup
    original_count = len(re.findall(r'except\s+\w+:\s+pass', content))
    
    # We won't automatically remove these as they might be intentional
    # Just report them for manual review
    stats['empty_except_pass_fixed'] += original_count
    
    return content, changes


def clean_commented_debug_code(content):
    """Remove commented-out debug print statements"""
    changes = 0
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove commented print statements that are obviously debug code
        if re.match(r'^\s*#\s*print\(', line):
            changes += 1
            continue
        # Remove commented logger debug calls
        if re.match(r'^\s*#\s*logger\.debug\(', line):
            changes += 1
            continue
        cleaned_lines.append(line)
    
    stats['comments_cleaned'] += changes
    return '\n'.join(cleaned_lines), changes


def clean_redundant_comments(content):
    """Remove obvious/redundant comments"""
    changes = 0
    lines = content.split('\n')
    cleaned_lines = []
    
    redundant_patterns = [
        r'^\s*#\s*Get\s+\w+\s+from\s+\w+\s*$',  # Get X from Y
        r'^\s*#\s*Set\s+\w+\s*$',  # Set X
        r'^\s*#\s*Check\s+if\s+\w+\s*$',  # Check if X
        r'^\s*#\s*Return\s+\w+\s*$',  # Return X
    ]
    
    for line in lines:
        is_redundant = False
        for pattern in redundant_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_redundant = True
                changes += 1
                break
        
        if not is_redundant:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), changes


def process_file(filepath):
    """Process a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        total_changes = 0
        
        # Apply cleanups
        content, changes = clean_commented_debug_code(content)
        total_changes += changes
        
        content, changes = clean_redundant_comments(content)
        total_changes += changes
        
        # Only write if there were changes
        if total_changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Cleaned {filepath.name}: {total_changes} improvements")
            stats['files_processed'] += 1
        
        return total_changes > 0
        
    except Exception as e:
        print(f"  ✗ Error processing {filepath}: {e}")
        return False


def main():
    """Main cleanup process"""
    print("=" * 70)
    print("CODE QUALITY CLEANUP")
    print("=" * 70)
    print()
    
    total_files_changed = 0
    
    for app in APPS:
        app_path = BASE_DIR / app
        if not app_path.exists():
            continue
        
        print(f"\n📁 Cleaning {app}...")
        
        # Find all Python files
        py_files = list(app_path.rglob('*.py'))
        
        for py_file in py_files:
            # Skip migrations and __pycache__
            if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            if process_file(py_file):
                total_files_changed += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Files modified: {stats['files_processed']}")
    print(f"Commented debug code removed: {stats['comments_cleaned']}")
    print(f"Empty except:pass blocks found: {stats['empty_except_pass_fixed']}")
    print()
    print("✅ Cleanup complete!")
    print()
    print("⚠️  RECOMMENDATIONS:")
    print("1. Review except:pass blocks manually - some may need proper error handling")
    print("2. Replace broad 'except Exception' with specific exceptions")
    print("3. Add docstrings to functions missing them")
    print("4. Run tests to ensure no functionality was broken")
    print("=" * 70)


if __name__ == '__main__':
    main()
