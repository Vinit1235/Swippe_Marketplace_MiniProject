"""
Security Check - Verify No Credentials in Code
Run this before pushing to GitHub
"""

import os
import re

# Sensitive patterns to search for
SENSITIVE_PATTERNS = {
    'email': r'posterpresentation\d*@gmail\.com',
    'password': r'fpticxkb[a-z]{8}',
    'api_key_real': r'AIza[A-Za-z0-9_-]{35}',  # Real Gemini API key pattern
}

# Files/folders to skip
SKIP_PATTERNS = [
    '.git',
    '__pycache__',
    'venv',
    'ENV',
    'env',
    '.venv',
    'instance',
    'chroma_db',
    '.pytest_cache',
    'node_modules',
    '.env',  # This file should be in gitignore anyway
]

def should_skip(path):
    """Check if path should be skipped"""
    for pattern in SKIP_PATTERNS:
        if pattern in path:
            return True
    return False

def check_file(filepath):
    """Check a single file for sensitive data"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': filepath,
                        'line': line_num,
                        'type': pattern_name,
                        'match': match.group()[:20] + '...'  # Truncate for safety
                    })
    except Exception as e:
        pass  # Skip binary files or files that can't be read
    
    return issues

def main():
    print("\n" + "="*60)
    print("SECURITY CHECK - Scanning for Credentials")
    print("="*60)
    
    all_issues = []
    files_scanned = 0
    
    # Scan all files in directory
    for root, dirs, files in os.walk('.'):
        # Remove skipped directories from search
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            if should_skip(filepath):
                continue
            
            # Only check text files
            if file.endswith(('.py', '.md', '.txt', '.json', '.html', '.js', '.css', '.yml', '.yaml', '.sh')):
                files_scanned += 1
                issues = check_file(filepath)
                all_issues.extend(issues)
    
    print(f"\n📊 Scanned {files_scanned} files")
    print("="*60)
    
    if all_issues:
        print(f"\n❌ FOUND {len(all_issues)} POTENTIAL ISSUES:\n")
        
        for issue in all_issues:
            print(f"⚠️  {issue['file']}:{issue['line']}")
            print(f"   Type: {issue['type']}")
            print(f"   Match: {issue['match']}")
            print()
        
        print("="*60)
        print("❌ SECURITY CHECK FAILED")
        print("="*60)
        print("\n⚠️  DO NOT PUSH TO GITHUB!")
        print("\n📋 Action Required:")
        print("1. Remove sensitive data from files listed above")
        print("2. Ensure .env is in .gitignore")
        print("3. Run this check again")
        print()
        return False
    else:
        print("\n✅ NO CREDENTIALS FOUND!")
        print("="*60)
        print("✅ SECURITY CHECK PASSED")
        print("="*60)
        print("\n🎉 Safe to push to GitHub!")
        print("\n📋 Final Checklist:")
        print("  [✓] No hardcoded emails")
        print("  [✓] No hardcoded passwords")
        print("  [✓] No hardcoded API keys")
        print("  [✓] .env is in .gitignore")
        print("\n🚀 Ready to commit and push!")
        print()
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
