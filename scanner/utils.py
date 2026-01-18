"""Utility functions for file operations, size checking, and report generation."""

import os
import shutil
import chardet
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


# Directories and files to exclude from scanning
EXCLUDED_DIRS = {'node_modules', 'build', 'dist', '.git', '__pycache__', '.venv', 'venv', 'env'}
EXCLUDED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib'}

# Text file extensions to prioritize
TEXT_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', '.yml', '.yaml', 
                   '.json', '.xml', '.html', '.css', '.sh', '.bash', '.zsh', '.md', '.txt', '.env', 
                   '.properties', '.conf', '.config', '.tf', '.tfvars', '.sql'}


def is_binary_file(filepath: str) -> bool:
    """
    Check if a file is binary by examining its extension and content.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file appears to be binary, False otherwise
    """
    file_path = Path(filepath)
    ext = file_path.suffix.lower()
    
    # Check extension first (fast check)
    if ext in EXCLUDED_EXTENSIONS:
        return True
    
    # Try to read and detect encoding
    try:
        with open(filepath, 'rb') as f:
            sample = f.read(1024)  # Read first 1KB
            if not sample:
                return False
            
            # Check for null bytes (binary indicator)
            if b'\x00' in sample:
                return True
            
            # Use chardet to detect encoding
            result = chardet.detect(sample)
            if result['encoding'] is None:
                return True
                
            # If confidence is low, likely binary
            if result['confidence'] < 0.7:
                return True
                
    except (IOError, PermissionError, UnicodeDecodeError):
        return True
    
    return False


def should_scan_file(filepath: str) -> bool:
    """
    Determine if a file should be scanned based on its path and type.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file should be scanned, False otherwise
    """
    file_path = Path(filepath)
    
    # Check if any parent directory is excluded
    for part in file_path.parts:
        if part in EXCLUDED_DIRS:
            return False
    
    # Don't scan binary files
    if is_binary_file(filepath):
        return False
    
    return True


def get_directory_size(directory: str) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, PermissionError):
        pass
    
    return total_size


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def cleanup_directory(directory: str) -> bool:
    """
    Recursively delete a directory and all its contents.
    
    Args:
        directory: Path to the directory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            return True
    except (OSError, PermissionError) as e:
        print(f"Error cleaning up directory {directory}: {e}")
        return False
    return False


def list_files_to_scan_agent(repo_path: str) -> List[str]:
    """
    Get list of files for agent to analyze (prioritized).
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Prioritized list of file paths
    """
    files_to_scan = []
    
    for root, dirs, files in os.walk(repo_path):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            filepath = os.path.join(root, file)
            if should_scan_file(filepath):
                files_to_scan.append(filepath)
    
    return prioritize_files(files_to_scan)


def prioritize_files(filepaths: List[str]) -> List[str]:
    """
    Prioritize files for scanning (config files first, then source code).
    
    Args:
        filepaths: List of file paths
        
    Returns:
        Prioritized list of file paths
    """
    config_files = []
    source_files = []
    other_files = []
    
    for filepath in filepaths:
        file_path = Path(filepath)
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Priority 1: Config files
        if (ext in {'.env', '.properties', '.conf', '.config', '.yaml', '.yml', '.json', '.tf', '.tfvars'} or
            name in {'.env', '.env.local', '.env.production', 'firebase.json', 'rules.json'} or
            'config' in name or 'firebase' in name):
            config_files.append(filepath)
        # Priority 2: Source code files
        elif ext in TEXT_EXTENSIONS:
            source_files.append(filepath)
        # Priority 3: Other text files
        else:
            other_files.append(filepath)
    
    return config_files + source_files + other_files


def export_findings_to_csv(findings: List[Dict], output_path: str) -> bool:
    """
    Export findings to a CSV file.
    
    Args:
        findings: List of finding dictionaries
        output_path: Path to output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not findings:
            return False
        
        df = pd.DataFrame(findings)
        
        # Ensure all expected columns exist
        expected_columns = ['file_name', 'line_number', 'risk_type', 'severity', 
                          'description', 'fix_suggestion', 'what_to_change', 'why_problem']
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns
        df = df[expected_columns]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False


def get_file_context(filepath: str, line_number: int, context_lines: int = 5) -> Dict[str, List[str]]:
    """
    Get surrounding context lines for a specific line in a file.
    
    Args:
        filepath: Path to the file
        line_number: Line number (1-indexed)
        context_lines: Number of lines before and after to include
        
    Returns:
        Dictionary with 'before', 'line', and 'after' lists of strings
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Convert to 0-indexed
        idx = line_number - 1
        
        start = max(0, idx - context_lines)
        end = min(len(lines), idx + context_lines + 1)
        
        before = [line.rstrip() for line in lines[start:idx]]
        line = lines[idx].rstrip() if idx < len(lines) else ''
        after = [line.rstrip() for line in lines[idx + 1:end]]
        
        return {
            'before': before,
            'line': line,
            'after': after,
            'line_number': line_number
        }
    except Exception as e:
        return {
            'before': [],
            'line': '',
            'after': [],
            'line_number': line_number,
            'error': str(e)
        }

