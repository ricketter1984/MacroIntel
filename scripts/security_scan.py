#!/usr/bin/env python3
"""
Security Scan Script for MacroIntel

This script performs security checks on the codebase to detect:
- Hardcoded credentials
- Insecure patterns
- Potential vulnerabilities
- API key exposure

Used by pre-commit hooks to prevent security issues from being committed.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Security patterns to detect
SECURITY_PATTERNS = {
 # API Keys and Tokens
 'api_key': r'(?i)(api_key|api_key|secret_key|access_key|private_key)\s*=\s*["\'][^"\']+["\']',
 'openai_key': r'sk-[a-zA-Z0-9]{48}',
 'github_token': r'ghp_[a-zA-Z0-9]{36}',
 'aws_key': r'AKIA[0-9A-Z]{16}',
 'google_key': r'AIza[0-9A-Za-z-_]{35}',
 'firebase_key': r'AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}',
 
 # Passwords and Secrets
 'password': r'(?i)password\s*=\s*["\'][^"\']+["\']',
 'secret': r'(?i)secret\s*=\s*["\'][^"\']+["\']',
 'token': r'(?i)token\s*=\s*["\'][^"\']+["\']',
 
 # Database credentials
 'db_password': r'(?i)(db_password|database_password|mysql_password|postgres_password)\s*=\s*["\'][^"\']+["\']',
 
 # URLs with credentials
 'url_with_auth': r'https?://[^/]+:[^@]+@[^/]+',
 
 # Private keys
 'private_key': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
 'ssh_key': r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----',
}

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
 r'\.git/',
 r'venv/',
 r'env/',
 r'\.venv/',
 r'\.env/',
 r'__pycache__/',
 r'\.pyc$',
 r'\.pyo$',
 r'\.pyd$',
 r'\.so$',
 r'\.dll$',
 r'\.exe$',
 r'\.bin$',
 r'\.log$',
 r'\.tmp$',
 r'\.temp$',
 r'\.cache$',
 r'\.secrets\.baseline$',
 r'security_audit_log\.md$',
 r'\.pre-commit-config\.yaml$',
]

# Safe patterns (false positives)
SAFE_PATTERNS = [
 r'os\.getenv\(',
 r'load_dotenv\(',
 r'API_KEY\s*=\s*os\.getenv\(',
 r'api_key\s*=\s*os\.getenv\(',
 r'#.*api_key',
 r'//.*api_key',
 r'/\*.*api_key',
 r'"""',
 r"'''",
 r'#.*password',
 r'//.*password',
 r'/\*.*password',
]

class SecurityScanner:
 def __init__(self):
 self.issues = []
 self.stats = {
 'files_scanned': 0,
 'issues_found': 0,
 'patterns_matched': {}
 }
 
 def should_exclude_file(self, file_path: str) -> bool:
 """Check if file should be excluded from scanning."""
 for pattern in EXCLUDE_PATTERNS:
 if re.search(pattern, file_path):
 return True
 return False
 
 def is_safe_pattern(self, line: str) -> bool:
 """Check if line contains safe patterns (false positives)."""
 for pattern in SAFE_PATTERNS:
 if re.search(pattern, line):
 return True
 return False
 
 def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
 """Scan a single file for security issues."""
 issues = []
 
 try:
 with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
 
 for line_num, line in enumerate(lines, 1):
 # Skip safe patterns
 if self.is_safe_pattern(line):
 continue
 
 # Check each security pattern
 for pattern_name, pattern in SECURITY_PATTERNS.items():
 matches = re.finditer(pattern, line)
 for match in matches:
 issue = {
 'file': file_path,
 'line': line_num,
 'pattern': pattern_name,
 'match': match.group(),
 'line_content': line.strip(),
 'severity': self.get_severity(pattern_name)
 }
 issues.append(issue)
 
 # Update stats
 self.stats['patterns_matched'][pattern_name] = \
 self.stats['patterns_matched'].get(pattern_name, 0) + 1
 
 except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}")
 
 return issues
 
 def get_severity(self, pattern_name: str) -> str:
 """Get severity level for a pattern."""
 high_severity = ['api_key', 'openai_key', 'github_token', 'aws_key', 'google_key', 'firebase_key']
 medium_severity = ['password', 'secret', 'token', 'db_password']
 low_severity = ['url_with_auth', 'private_key', 'ssh_key']
 
 if pattern_name in high_severity:
 return 'HIGH'
 elif pattern_name in medium_severity:
 return 'MEDIUM'
 elif pattern_name in low_severity:
 return 'LOW'
 else:
 return 'INFO'
 
 def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
 """Scan a directory recursively for security issues."""
 all_issues = []
 
 for root, dirs, files in os.walk(directory):
 # Skip excluded directories
 dirs[:] = [d for d in dirs if not self.should_exclude_file(os.path.join(root, d))]
 
 for file in files:
 file_path = os.path.join(root, file)
 
 # Skip excluded files
 if self.should_exclude_file(file_path):
 continue
 
 # Only scan text files
 if self.is_text_file(file_path):
 self.stats['files_scanned'] += 1
 issues = self.scan_file(file_path)
 all_issues.extend(issues)
 
 return all_issues
 
 def is_text_file(self, file_path: str) -> bool:
 """Check if file is a text file that should be scanned."""
 text_extensions = {
 '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml',
 '.md', '.txt', '.cfg', '.conf', '.ini', '.toml', '.sh', '.bash',
 '.ps1', '.bat', '.cmd', '.dockerfile', '.dockerignore',
 '.gitignore', '.gitattributes', '.editorconfig'
 }
 
 ext = Path(file_path).suffix.lower()
 return ext in text_extensions
 
 def generate_report(self, issues: List[Dict[str, Any]]) -> str:
 """Generate a security report."""
 if not issues:
 return " No security issues found!"
 
 report = []
 report.append("🚨 SECURITY ISSUES FOUND!")
 report.append("=" * 50)
 
 # Group by severity
 by_severity = {}
 for issue in issues:
 severity = issue['severity']
 if severity not in by_severity:
 by_severity[severity] = []
 by_severity[severity].append(issue)
 
 # Report by severity
 for severity in ['HIGH', 'MEDIUM', 'LOW', 'INFO']:
 if severity in by_severity:
 report.append(f"\n{severity} SEVERITY ISSUES:")
 report.append("-" * 30)
 
 for issue in by_severity[severity]:
 report.append(f"File: {issue['file']}:{issue['line']}")
 report.append(f"Pattern: {issue['pattern']}")
 report.append(f"Match: {issue['match'][:50]}...")
 report.append(f"Line: {issue['line_content'][:100]}...")
 report.append("")
 
 # Summary
 report.append("SUMMARY:")
 report.append("-" * 20)
 report.append(f"Files scanned: {self.stats['files_scanned']}")
 report.append(f"Total issues: {len(issues)}")
 report.append(f"High severity: {len(by_severity.get('HIGH', []))}")
 report.append(f"Medium severity: {len(by_severity.get('MEDIUM', []))}")
 report.append(f"Low severity: {len(by_severity.get('LOW', []))}")
 
 return "\n".join(report)
 
 def run_scan(self, target: str = ".") -> int:
 """Run the security scan and return exit code."""
 print(f"🔍 Scanning {target} for security issues...")
 
 # Scan the target
 if os.path.isfile(target):
 issues = self.scan_file(target)
 else:
 issues = self.scan_directory(target)
 
 # Generate report
 report = self.generate_report(issues)
 print(report)
 
 # Return exit code (0 for success, 1 for issues found)
 return 0 if not issues else 1

def main():
    """Main entry point for the security scanner."""
 import argparse
 
 parser = argparse.ArgumentParser(description="Security Scanner for MacroIntel")
 parser.add_argument('target', nargs='?', default='.', help='File or directory to scan')
 parser.add_argument('--json', action='store_true', help='Output results in JSON format')
 parser.add_argument('--report', action='store_true', help='Generate detailed report')
 
 args = parser.parse_args()
 
 scanner = SecurityScanner()
 exit_code = scanner.run_scan(args.target)
 
 if args.json:
 # Output JSON for programmatic use
 result = {
 'issues': scanner.issues,
 'stats': scanner.stats,
 'success': exit_code == 0
 }
 print(json.dumps(result, indent=2))
 
 sys.exit(exit_code)

if __name__ == "__main__":
    main() 