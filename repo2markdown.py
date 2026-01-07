#!/usr/bin/env python3
"""
Git Repository to Markdown Exporter

This script traverses a local git repository and creates a markdown file containing:
1. A table of contents with all folders and files (with line ranges)
2. The content of each tracked file (respecting .gitignore)

Usage:
    python repo_to_markdown.py [repo_path] [output_file]
    
    repo_path   - Path to the git repository (default: current directory)
    output_file - Output markdown file (default: repo_contents.md)
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Generator


def get_tracked_files(repo_path: str) -> set[str]:
    """Get all files tracked by git (not ignored)."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except subprocess.CalledProcessError as e:
        print(f"Error: Not a git repository or git command failed: {e}")
        sys.exit(1)


def is_binary_file(filepath: str) -> bool:
    """Check if a file is binary by reading its first chunk."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
            # Check for null bytes (common indicator of binary)
            if b'\x00' in chunk:
                return True
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (IOError, OSError):
        return True


def get_file_content(filepath: str) -> str | None:
    """Read and return file content, or None if binary/unreadable."""
    if is_binary_file(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except (IOError, OSError) as e:
        return f"[Error reading file: {e}]"


def build_directory_tree(files: set[str]) -> dict:
    """Build a nested dictionary representing the directory structure."""
    tree = {}
    for filepath in sorted(files):
        parts = Path(filepath).parts
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        # Mark files with None value
        current[parts[-1]] = None
    return tree


def generate_tree_lines(tree: dict, prefix: str = "", is_last: bool = True) -> Generator[str, None, None]:
    """Generate tree view lines for the directory structure."""
    items = list(tree.items())
    for i, (name, subtree) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = "└── " if is_last_item else "├── "
        
        if subtree is None:
            # It's a file
            yield f"{prefix}{connector}📄 {name}"
        else:
            # It's a directory
            yield f"{prefix}{connector}📁 {name}/"
            extension = "    " if is_last_item else "│   "
            yield from generate_tree_lines(subtree, prefix + extension, is_last_item)


def create_markdown(repo_path: str, output_file: str) -> None:
    """Create the markdown file with TOC and file contents."""
    repo_path = os.path.abspath(repo_path)
    repo_name = os.path.basename(repo_path)
    
    # Get tracked files
    tracked_files = get_tracked_files(repo_path)
    if not tracked_files:
        print("No tracked files found in the repository.")
        sys.exit(1)
    
    print(f"Found {len(tracked_files)} tracked files")
    
    # Build directory tree
    tree = build_directory_tree(tracked_files)
    
    # First pass: calculate line numbers for each file
    # We need to build the content first to know line ranges
    file_contents = {}
    for filepath in sorted(tracked_files):
        full_path = os.path.join(repo_path, filepath)
        content = get_file_content(full_path)
        file_contents[filepath] = content
    
    # Build the document structure to calculate line numbers
    # Header section
    header_lines = [
        f"# Repository: {repo_name}",
        "",
        f"**Path:** `{repo_path}`",
        "",
        f"**Total tracked files:** {len(tracked_files)}",
        "",
        "---",
        "",
    ]
    
    # Directory structure section
    structure_lines = [
        "## 📂 Directory Structure",
        "",
        "```",
        f"{repo_name}/",
    ]
    structure_lines.extend(generate_tree_lines(tree))
    structure_lines.extend(["```", "", "---", ""])
    
    # TOC header
    toc_header = [
        "## 📑 Table of Contents",
        "",
        "| File | Lines | Type |",
        "|------|-------|------|",
    ]
    
    # Calculate starting line for file contents
    # We need to account for TOC entries (one per file)
    num_toc_entries = len(tracked_files)
    
    # Lines before file contents section
    pre_content_lines = (
        len(header_lines) + 
        len(structure_lines) + 
        len(toc_header) + 
        num_toc_entries +  # TOC entries
        3  # Empty line, separator, empty line after TOC
    )
    
    # File contents section header
    content_section_header = [
        "",
        "---",
        "",
        "## 📄 File Contents",
        "",
    ]
    pre_content_lines += len(content_section_header)
    
    # Calculate line ranges for each file
    # We'll do a two-pass approach: build content first, then calculate actual line numbers
    file_line_ranges = {}
    current_line = pre_content_lines + 1  # 1-indexed
    
    for filepath in sorted(tracked_files):
        content = file_contents[filepath]
        ext = Path(filepath).suffix.lstrip('.') or 'txt'
        
        if content is None:
            # Binary file
            content_lines = 1  # "[Binary file - content not displayed]"
            file_type = "binary"
        else:
            # Count actual lines in content (without trailing newline)
            content_lines = len(content.rstrip('\n').split('\n'))
            file_type = "text"
        
        # Structure of each file entry:
        # Line 1: ### filename
        # Line 2: (empty)
        # Line 3: **Path:** `filepath`
        # Line 4: (empty)
        # Line 5: ```ext
        # Lines 6 to 6+content_lines-1: content
        # Line 6+content_lines: ```
        # Line 7+content_lines: (empty)
        # Line 8+content_lines: ---
        # Line 9+content_lines: (empty)
        
        start_line = current_line
        total_file_lines = 4 + 1 + content_lines + 1 + 3  # header(4) + fence_start(1) + content + fence_end(1) + spacing(3)
        end_line = current_line + total_file_lines - 1
        
        file_line_ranges[filepath] = (start_line, end_line, file_type)
        current_line = end_line + 1
    
    # Now build the final document
    output_lines = []
    output_lines.extend(header_lines)
    output_lines.extend(structure_lines)
    output_lines.extend(toc_header)
    
    # Add TOC entries with line ranges
    for filepath in sorted(tracked_files):
        start, end, file_type = file_line_ranges[filepath]
        # Create anchor-friendly name
        anchor = filepath.replace('/', '-').replace('.', '-').replace('_', '-').lower()
        icon = "📄" if file_type == "text" else "📦"
        output_lines.append(f"| {icon} [{filepath}](#{anchor}) | {start}-{end} | {file_type} |")
    
    output_lines.extend(content_section_header)
    
    # Add file contents
    for filepath in sorted(tracked_files):
        content = file_contents[filepath]
        ext = Path(filepath).suffix.lstrip('.') or 'txt'
        anchor = filepath.replace('/', '-').replace('.', '-').replace('_', '-').lower()
        
        output_lines.append(f"### {filepath}")
        output_lines.append("")
        output_lines.append(f"**Path:** `{filepath}`")
        output_lines.append("")
        
        if content is None:
            output_lines.append("```")
            output_lines.append("[Binary file - content not displayed]")
        else:
            output_lines.append(f"```{ext}")
            output_lines.append(content.rstrip('\n'))
        
        output_lines.append("```")
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ Successfully created: {output_file}")
    print(f"   - Total lines: {len(output_lines)}")
    print(f"   - Files documented: {len(tracked_files)}")


def main():
    # Parse arguments
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "repo_contents.md"
    
    # Validate repo path
    if not os.path.isdir(repo_path):
        print(f"Error: '{repo_path}' is not a valid directory")
        sys.exit(1)
    
    # Check if it's a git repo
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"Error: '{repo_path}' is not a git repository (no .git directory found)")
        sys.exit(1)
    
    create_markdown(repo_path, output_file)


if __name__ == "__main__":
    main()
