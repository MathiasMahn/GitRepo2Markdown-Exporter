# Repo to Markdown

A Python script that exports an entire git repository into a single, well-organized markdown file. Perfect for sharing codebases with LLMs, creating documentation snapshots, or archiving project states.

## Features

- **Git-aware**: Only includes tracked files, automatically respecting `.gitignore`
- **Customizable filtering**: Use `.repotomdrc` to exclude or include specific files
- **Visual directory tree**: Shows folder structure with intuitive icons
- **Table of contents**: Clickable links with line ranges for quick navigation
- **Syntax highlighting**: Code blocks use appropriate language tags based on file extensions
- **Binary detection**: Automatically skips binary files with a placeholder note
- **Zero dependencies**: Uses only Python standard library + git

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/repo-to-markdown.git
cd repo-to-markdown

# Make the script executable (optional)
chmod +x repo_to_markdown.py
```

**Requirements:**
- Python 3.10+
- Git installed and available in PATH

## Usage

```bash
python repo_to_markdown.py [repo_path] [output_file]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `repo_path` | `.` (current directory) | Path to the git repository |
| `output_file` | `repo_contents.md` | Output markdown filename |

### Examples

```bash
# Export current directory
python repo_to_markdown.py

# Export a specific repository
python repo_to_markdown.py /path/to/my-project

# Export with custom output filename
python repo_to_markdown.py ./my-project project-snapshot.md
```

## Configuration

Create a `.repotomdrc` file in your repository root to customize which files are included in the output.

### File Format

```ini
[exclude]
# Patterns for files to exclude (in addition to .gitignore)
# These files won't appear in the markdown output

[include]
# Patterns for files to include (overrides .gitignore)
# Use this to add gitignored files to the output
```

### Pattern Syntax

Patterns follow gitignore-style matching:

| Pattern | Matches |
|---------|---------|
| `*.log` | All `.log` files in any directory |
| `docs/*` | All files directly in the `docs/` folder |
| `docs/**` | All files anywhere under `docs/` |
| `test_*.py` | Files starting with `test_` ending in `.py` |
| `config/?.json` | Single character matches like `config/a.json` |
| `[abc].txt` | Matches `a.txt`, `b.txt`, or `c.txt` |

### Example Configuration

```ini
[exclude]
# Don't include test files in documentation
tests/*
*_test.py
*.spec.js

# Exclude build artifacts that might be tracked
dist/*
build/*

# Exclude sensitive configs
.env
secrets.json
config/local.yaml

[include]
# Include example env file even though .env* is gitignored
.env.example

# Include sample configs
*.sample
config/*.example.yaml
```

### Behavior Notes

- The `.repotomdrc` file itself is automatically excluded from output
- `[include]` patterns can pull in gitignored files
- `[exclude]` patterns only affect git-tracked files
- Patterns are applied in order: tracked files → minus excludes → plus includes

## Output Format

The generated markdown file contains:

1. **Header** — Repository name, path, and file count
2. **Directory Structure** — Visual tree of all folders and files
3. **Table of Contents** — Links to each file with line ranges
4. **File Contents** — Full source code with syntax highlighting

### Example Output

```markdown
# Repository: my-project

**Path:** `/home/user/my-project`
**Total tracked files:** 12

---

## 📂 Directory Structure

\```
my-project/
├── 📄 README.md
├── 📁 src/
│   ├── 📄 main.py
│   └── 📄 utils.py
└── 📁 tests/
    └── 📄 test_main.py
\```

## 📑 Table of Contents

| File | Lines | Type |
|------|-------|------|
| 📄 [README.md](#readme-md) | 25-40 | text |
| 📄 [src/main.py](#src-main-py) | 41-85 | text |
...

## 📄 File Contents

### src/main.py

**Path:** `src/main.py`

\```py
def main():
    print("Hello, World!")
\```
```

## Use Cases

- **LLM Context**: Feed entire codebases to AI assistants in a single file
- **Code Reviews**: Share a complete project snapshot for review
- **Documentation**: Generate a browsable archive of your codebase
- **Onboarding**: Help new team members understand project structure
- **Archival**: Create point-in-time snapshots of repositories

## How It Works

1. Runs `git ls-files` to get all tracked files (respects `.gitignore`)
2. Builds a nested directory tree structure
3. Calculates line ranges by pre-computing content lengths
4. Generates the final markdown with TOC, tree view, and file contents

## Limitations

- Requires the target directory to be a git repository
- Binary files are detected and skipped (placeholder shown instead)
- Very large repositories may produce unwieldy output files
- Line range links work best in markdown viewers that support anchor links

## License

MIT License — feel free to use, modify, and distribute.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.