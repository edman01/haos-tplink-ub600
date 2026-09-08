"""Check tracked publication files, reporting rule names but never secret text."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FILES = {
    '.gitattributes', '.gitignore', 'LICENSE', 'repository.yaml',
    'README.md', 'SECURITY.md', 'CONTRIBUTING.md',
    'RELEASE_NOTES.md', '.github/ISSUE_TEMPLATE/bug_report.md',
    '.github/workflows/tests.yml', 'ub600_compat/.dockerignore',
    'ub600_compat/config.yaml', 'ub600_compat/Dockerfile',
    'ub600_compat/README.md', 'ub600_compat/DOCS.md',
    'ub600_compat/CHANGELOG.md', 'ub600_compat/patch_btusb.py',
    'ub600_compat/run.py', 'ub600_compat/compatibility.py',
    'tests/test_patch_btusb.py', 'tests/test_loader.py',
    'tests/test_publication.py', 'tools/check_publication.py',
}
PATTERNS = {
    'device MAC address': re.compile(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b'),
    'private IPv4 address': re.compile(r'\b(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b'),
    'personal Windows path': re.compile(r'(?i)[a-z]:[\\/]+Users[\\/]+[^\s]+'),
    'personal Unix path': re.compile(r'/(?:home|Users)/[^\s/]+/'),
    'private key material': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'GitHub credential': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'JWT-like credential': re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b'),
    'external email address': re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
}


def inspect_text(text):
    return [label for label, pattern in PATTERNS.items() if pattern.search(text)]


def publication_files():
    # Never accidentally enumerate a surrounding repository's files.
    if (ROOT / '.git').exists():
        tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT,
                                 check=True, capture_output=True).stdout
        return [name for name in tracked.decode().split('\x00') if name]
    return sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob('*')
                  if path.is_file() and '__pycache__' not in path.parts)


def check():
    files = publication_files()
    problems = []
    for name in files:
        if name not in ALLOWED_FILES:
            problems.append((name, 'file not in publication allowlist'))
            continue
        path = ROOT / name
        if path.is_symlink():
            problems.append((name, 'symbolic link not allowed'))
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeError:
            problems.append((name, 'binary/non-UTF-8 file not allowed'))
            continue
        problems.extend((name, rule) for rule in inspect_text(text))
    for missing in sorted(ALLOWED_FILES - set(files)):
        problems.append((missing, 'required publication file missing'))
    if problems:
        for name, rule in problems:
            print(f'FAIL {name}: {rule}')
        return 1
    print(f'PASS: {len(files)} allowlisted UTF-8 source/documentation files; no flagged personal data or credential patterns.')
    print('This heuristic check supplements, but does not replace, manual file and Git-metadata review.')
    return 0


if __name__ == '__main__':
    sys.exit(check())
