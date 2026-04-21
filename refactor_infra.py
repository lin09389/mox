import os
import shutil
import re
from pathlib import Path

# Paths
base_dir = Path(r"c:\Users\JHJ\Desktop\mox")
core_dir = base_dir / "mox" / "core"
infra_dir = base_dir / "mox" / "infrastructure"

# 1. Create infrastructure directory
infra_dir.mkdir(parents=True, exist_ok=True)
init_file = infra_dir / "__init__.py"
if not init_file.exists():
    init_file.write_text('"""Infrastructure and cross-cutting concerns."""\n', encoding='utf-8')

# 2. Define modules to move
infra_modules = [
    "database", "cache", "advanced_cache", "logging", "monitoring",
    "observability", "telemetry", "sandbox", "plugin", "config",
    "utils", "auth", "audit", "scheduler", "tasks", "cicd", "report"
]

core_modules = [
    "chinese_llm", "evaluation", "exceptions", "llm", "llm_router", 
    "patterns", "prompt_protection", "rag_isolation", "security_guard",
    "similarity", "types", "version", "workflow"
]

# 3. Move the files (Use os.rename or shutil.move since git mv might fail if not fully git-tracked or permission issues)
# We will just move them. Git will detect them as renamed later when user commits.
for mod in infra_modules:
    src = core_dir / f"{mod}.py"
    dst = infra_dir / f"{mod}.py"
    if src.exists():
        shutil.move(str(src), str(dst))
        print(f"Moved {src.name} to infrastructure/")

# Helper function to rewrite imports in a file
def rewrite_imports(filepath, is_in_infra, is_in_core):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Global absolutes replacements (for ALL files)
    for mod in infra_modules:
        content = re.sub(rf'from\s+mox\.core\.{mod}\s+import', f'from mox.infrastructure.{mod} import', content)
        content = re.sub(rf'import\s+mox\.core\.{mod}(\s|$)', rf'import mox.infrastructure.{mod}\1', content)

    # Specific relative imports replacement
    if is_in_infra:
        # In infra, if it imports a core module relatively, make it absolute to mox.core
        for mod in core_modules:
            content = re.sub(rf'from\s+\.{mod}\s+import', f'from mox.core.{mod} import', content)
    
    elif is_in_core:
        # In core, if it imports an infra module relatively, make it absolute to mox.infrastructure
        for mod in infra_modules:
            content = re.sub(rf'from\s+\.{mod}\s+import', f'from mox.infrastructure.{mod} import', content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated imports in {filepath}")

# 4. Process all Python files in the project
for root, dirs, files in os.walk(base_dir):
    # skip .git, __pycache__, etc
    if ".git" in root or "__pycache__" in root or ".pytest_cache" in root or ".venv" in root:
        continue
        
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            is_in_infra = "mox\\infrastructure" in filepath or "mox/infrastructure" in filepath
            is_in_core = "mox\\core" in filepath or "mox/core" in filepath
            rewrite_imports(filepath, is_in_infra, is_in_core)

# 5. Fix mox/core/__init__.py manually
core_init = core_dir / "__init__.py"
if core_init.exists():
    with open(core_init, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # We will remove any exports from infra modules
    new_lines = []
    skip = False
    for line in lines:
        if any(f"from .{mod} import" in line for mod in infra_modules):
            skip = True
            if "(" in line and ")" not in line:
                continue # Multiline import start
        if skip:
            if ")" in line:
                skip = False
            continue
            
        new_lines.append(line)
        
    with open(core_init, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Cleaned up mox/core/__init__.py")

print("Refactoring complete.")
