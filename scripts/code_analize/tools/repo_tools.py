import os
from langchain.tools import tool

@tool
def list_files(root: str, max_depth: int = 10) -> list:
    """List files in the repository with max depth."""
    result = []

    for current, dirs, files in os.walk(root):
        depth = current.replace(root, "").count(os.sep)
        if depth > max_depth:
            dirs[:] = []     # stop deeper walk
            continue

        for f in files:
            full = os.path.join(current, f)
            rel = os.path.relpath(full, root)
            result.append(rel)

    return result


@tool
def read_file(root: str, path: str) -> str:
    """Read a file safely."""
    full_path = os.path.join(root, path)

    if not os.path.isfile(full_path):
        return f"ERROR: {path} does not exist."

    try:
        with open(full_path, "r", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {e}"


@tool
def detect_languages(root: str) -> list:
    """Detect languages in the repo."""
    exts = set()

    for current, dirs, files in os.walk(root):
        for f in files:
            ext = f.split(".")[-1].lower()
            exts.add(ext)

    mapping = {
        "java": "Java",
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "php": "PHP",
        "rb": "Ruby",
        "go": "Go",
        "rs": "Rust",
        "cs": "C#",
    }

    langs = sorted({mapping[e] for e in exts if e in mapping})
    return langs


@tool
def search_files(root: str, filename: str, extensions: str = "*") -> list:
    """
    Search for files by name pattern in the repository.
    
    Args:
        root: Repository root path
        filename: Filename or pattern to search (case-insensitive)
        extensions: File extensions to include (comma-separated, default: all)
    
    Returns:
        List of matching file paths relative to root
    """
    matches = []
    filename_lower = filename.lower()
    ext_list = [e.strip().lower() for e in extensions.split(",")] if extensions != "*" else None
    
    for current, dirs, files in os.walk(root):
        for f in files:
            # Check filename match
            if filename_lower in f.lower():
                # Check extension if specified
                if ext_list is None or any(f.lower().endswith(f".{ext}") for ext in ext_list):
                    full = os.path.join(current, f)
                    rel = os.path.relpath(full, root)
                    matches.append(rel)
    
    return matches


@tool
def grep_search(root: str, pattern: str, file_pattern: str = "*") -> list:
    """
    Search for content/pattern within files.
    
    Args:
        root: Repository root path
        pattern: Text pattern to search for (case-insensitive)
        file_pattern: File pattern to search in (e.g., "*.java", "*.py")
    
    Returns:
        List of results with format [file_path:line_number:matching_line]
    """
    results = []
    pattern_lower = pattern.lower()
    
    for current, dirs, files in os.walk(root):
        for f in files:
            # Check if file matches pattern
            if file_pattern == "*" or f.endswith(file_pattern.replace("*", "")):
                full = os.path.join(current, f)
                rel = os.path.relpath(full, root)
                
                try:
                    with open(full, "r", errors="ignore") as file:
                        for line_num, line in enumerate(file, 1):
                            if pattern_lower in line.lower():
                                results.append(f"{rel}:{line_num}:{line.strip()}")
                except Exception:
                    pass
    
    return results


@tool
def tree_structure(root: str, max_depth: int = 20, ignore_dirs: str = ".git,.mvn,node_modules,.venv,target,build,__pycache__") -> str:
    """
    Generate a tree-like structure of the repository showing all directories and files.
    
    Args:
        root: Repository root path
        max_depth: Maximum depth to traverse
        ignore_dirs: Comma-separated list of directories to ignore
    
    Returns:
        Tree-formatted string showing complete project structure
    """
    ignore_list = [d.strip() for d in ignore_dirs.split(",")]
    
    def build_tree(path, prefix="", depth=0):
        if depth > max_depth:
            return ""
        
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return ""
        
        # Separate dirs and files
        dirs = []
        files = []
        
        for entry in entries:
            if entry.startswith(".") and entry not in [".gitignore", ".env"]:
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                if entry not in ignore_list:
                    dirs.append(entry)
            else:
                files.append(entry)
        
        tree_str = ""
        # Add files first
        for i, file in enumerate(sorted(files)):
            is_last = (i == len(files) - 1) and len(dirs) == 0
            connector = "└── " if is_last else "├── "
            tree_str += f"{prefix}{connector}{file}\n"
        
        # Add directories
        for i, dir_name in enumerate(sorted(dirs)):
            is_last = i == len(dirs) - 1
            connector = "└── " if is_last else "├── "
            tree_str += f"{prefix}{connector}{dir_name}/\n"
            
            extension = "    " if is_last else "│   "
            full_path = os.path.join(path, dir_name)
            tree_str += build_tree(full_path, prefix + extension, depth + 1)
        
        return tree_str
    
    return f"{os.path.basename(root)}/\n" + build_tree(root)
