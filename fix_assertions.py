#!/usr/bin/env python3
"""
Script to fix incorrect assertion method names in test files
"""

import os
import re

def fix_assertions_in_file(filepath):
    """Fix assertion method names in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Define the replacements
    replacements = {
        'assert_Greater': 'assertGreater',
        'assert_Less': 'assertLess', 
        'assert_In': 'assertIn',
        'skip_Test': 'skipTest',
        'assert_Equal': 'assertEqual',
        'assert_True': 'assertTrue',
        'assert_False': 'assertFalse'
    }
    
    # Apply replacements
    modified = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(f'self.{old}', f'self.{new}')
            modified = True
    
    # Write back if modified
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed assertions in {filepath}")
        return True
    return False

def main():
    """Fix assertions in all test files"""
    test_dirs = ['tests/integration', 'tests/performance']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for filename in os.listdir(test_dir):
                if filename.endswith('.py'):
                    filepath = os.path.join(test_dir, filename)
                    fix_assertions_in_file(filepath)

if __name__ == '__main__':
    main()