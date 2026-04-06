#!/usr/bin/env python3
"""
Cleanup script for TravelGuide project.
This script removes unnecessary files and directories to simplify the project structure.
"""
import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Directories to remove (relative to BASE_DIR)
DIRS_TO_REMOVE = [
    # Build and distribution directories
    'build',
    'dist',
    '*.egg-info',
    
    # Cache and temporary files
    '.pytest_cache',
    '.mypy_cache',
    '.cache',
    '.ipynb_checkpoints',
    
    # Development environment
    'venv',
    'env',
    '.venv',
    'ENV',
    
    # IDE specific
    '.vscode',
    '.idea',
    '*.sublime-*',
    
    # Documentation
    'docs/_build',
    
    # Logs
    'logs',
    
    # Temporary files
    'tmp',
    'temp',
    
    # Old migrations (keep the latest ones)
    '**/migrations/__pycache__',
    '**/migrations/*.py[co]',
    
    # Python cache
    '**/__pycache__',
    
    # Test coverage
    'htmlcov',
    '.coverage',
    
    # OS specific
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
]

# File patterns to remove
FILES_TO_REMOVE = [
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '*.so',
    '*~',
    '*.swp',
    '*.swo',
    '*.bak',
    '*.log',
    '*.sqlite3',
    '*.sql',
    '*.db',
    '*.orig',
    '*.rej',
]

def remove_paths(patterns, is_dir=True):
    """Remove files or directories matching the given patterns."""
    removed = []
    for pattern in patterns:
        for path in BASE_DIR.glob(pattern):
            try:
                if is_dir and path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                    removed.append(str(path))
                elif not is_dir and path.is_file():
                    path.unlink()
                    removed.append(str(path))
            except Exception as e:
                print(f"Error removing {path}: {e}")
    return removed

def main():
    print("Cleaning up project...\n")
    
    # Remove directories
    print("Removing directories:")
    dirs_removed = remove_paths(DIRS_TO_REMOVE, is_dir=True)
    for d in dirs_removed:
        print(f"  - {d}")
    
    # Remove files
    print("\nRemoving files:")
    files_removed = remove_paths(FILES_TO_REMOVE, is_dir=False)
    for f in files_removed:
        print(f"  - {f}")
    
    # Clean up empty directories
    print("\nCleaning up empty directories...")
    for root, dirs, _ in os.walk(BASE_DIR, topdown=False):
        for dir_name in dirs:
            try:
                dir_path = Path(root) / dir_name
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"  - Removed empty directory: {dir_path}")
            except Exception as e:
                print(f"Error removing {dir_path}: {e}")
    
    print("\nCleanup complete!")

if __name__ == "__main__":
    main()
