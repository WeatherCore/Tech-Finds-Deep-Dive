#!/usr/bin/env python3
"""读项目核心文件,产出结构化项目摘要供 tech-finds-deep-dive skill 的 LLM 推理用。

读取范围:README + 技术栈 + 主入口 + 架构文档/关键模块(不读测试用例,避免 context 爆炸)。
本脚本是可选加速:不可用时(Python 缺失/路径不可解析),LLM 用 Read 工具按相同范围读取,不中断流程。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 技术栈识别文件:文件名 -> 栈类型
STACK_FILES = {
    "package.json": "node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java-maven",
    "build.gradle": "java-gradle",
    "build.gradle.kts": "java-gradle",
    "composer.json": "php",
    "Gemfile": "ruby",
    "mix.exs": "elixir",
    "pubspec.yaml": "flutter",
    "Package.swift": "swift",
    "CMakeLists.txt": "cpp-cmake",
    "Makefile": "make",
}

# README 候选(按优先级)。SKILL.md 作为 fallback——
# 推广对象含 skill 本身时,skill 项目通常无 README,核心文档是 SKILL.md
README_CANDIDATES = [
    "README.md", "README.rst", "README.txt", "README",
    "readme.md", "readme.rst", "readme.txt", "readme",
    "SKILL.md",  # skill 项目 fallback
]

# 主入口候选(按语言)
ENTRY_CANDIDATES = {
    "python": ["main.py", "app.py", "run.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py", "cli.py"],
    "node": ["index.js", "index.ts", "main.js", "main.ts", "app.js", "app.ts", "src/index.js", "src/index.ts", "src/main.ts"],
    "go": ["main.go", "cmd/main.go"],
    "rust": ["src/main.rs", "src/lib.rs"],
    "java-maven": ["src/main/java/Main.java", "src/main/java/Application.java", "src/main/java/App.java"],
    "java-gradle": ["src/main/java/Main.java", "src/main/java/Application.java", "src/main/java/App.java"],
    "php": ["index.php", "public/index.php", "artisan"],
    "ruby": ["main.rb", "lib/main.rb"],
    "elixir": ["lib/application.ex"],
    "flutter": ["lib/main.dart"],
    "swift": ["Sources/main.swift"],
    "cpp-cmake": ["src/main.cpp", "src/main.c", "main.cpp", "main.c"],
    "make": ["Makefile"],
}

# 架构文档候选
ARCH_CANDIDATES = [
    "ARCHITECTURE.md", "DESIGN.md", "docs/architecture.md",
    "docs/design.md", "docs/README.md", "DESIGN.rst", "ARCHITECTURE.rst",
]

# 关键模块目录(扫一层,只列名不读内容)
KEY_DIRS = ["src", "lib", "core", "internal", "pkg", "app", "components", "modules", "cmd"]

# 单文件最多读 50KB,避免 context 爆炸
MAX_FILE_SIZE = 50 * 1024


def detect_stack(root: Path) -> dict:
    """识别技术栈,返回 {stack_type: {file, info}}"""
    found = {}
    for fname, stack_type in STACK_FILES.items():
        fpath = root / fname
        if fpath.exists() and fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                info = extract_stack_info(fname, content, stack_type)
                found[stack_type] = {"file": fname, "info": info}
            except Exception:
                pass
    return found


def _parse_pyproject(content: str) -> dict:
    """解析 pyproject.toml: 提取 [project] 基本信息与依赖。"""
    info: dict = {"name": "", "version": "", "description": "", "dependencies": []}
    in_project = False
    deps: list[str] = []
    collecting_deps = False
    deps_buffer = ""

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("[project"):
            in_project = True
            i += 1
            continue
        if stripped.startswith("[") and "]" in stripped:
            in_project = False
            i += 1
            continue
        if not in_project:
            i += 1
            continue
        if stripped.startswith("name") and "=" in stripped:
            info["name"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("version") and "=" in stripped:
            info["version"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("description") and "=" in stripped:
            info["description"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("dependencies") and "=" in stripped:
            deps_text = stripped.split("=", 1)[1].strip()
            if deps_text.startswith("["):
                deps_buffer = deps_text
                collecting_deps = True
                if deps_text.endswith("]"):
                    deps += _extract_quoted_items(deps_buffer)
                    collecting_deps = False
                    deps_buffer = ""
        elif collecting_deps:
            deps_buffer += " " + stripped
            if stripped.endswith("]"):
                deps += _extract_quoted_items(deps_buffer)
                collecting_deps = False
                deps_buffer = ""
        i += 1
    info["dependencies"] = deps[:25]
    return info


def _extract_quoted_items(text: str) -> list[str]:
    """从 ["a", "b"] 这种单行/多行数组中提取引号内字符串。"""
    items: list[str] = []
    current = ""
    in_quote = False
    quote_char = ""
    for ch in text:
        if ch in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
                items.append(current)
                current = ""
            continue
        if in_quote:
            current += ch
    return items


def _parse_go_mod(content: str) -> dict:
    """解析 go.mod: 正确提取 module 与 require 块/单行依赖。"""
    info: dict = {"module": "", "requires": []}
    in_require_block = False

    for line in content.splitlines():
        ls = line.strip()
        if not ls or ls.startswith("//"):
            continue
        if ls.startswith("module "):
            info["module"] = ls[7:].strip()
            continue
        if ls == "require (":
            in_require_block = True
            continue
        if in_require_block and ls == ")":
            in_require_block = False
            continue
        if in_require_block:
            # 块内每行: module version [// indirect]
            parts = ls.split()
            if parts:
                info["requires"].append(parts[0])
            continue
        if ls.startswith("require "):
            parts = ls[8:].split()
            if parts:
                info["requires"].append(parts[0])

    info["requires"] = info["requires"][:25]
    return info


def _parse_cargo(content: str) -> dict:
    """解析 Cargo.toml: 提取 [package] 信息与 [dependencies]。"""
    info: dict = {"name": "", "version": "", "description": "", "dependencies": []}
    in_package = False
    in_deps = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[package]"):
            in_package = True
            in_deps = False
            continue
        if stripped.startswith("[dependencies]"):
            in_package = False
            in_deps = True
            continue
        if stripped.startswith("[") and "]" in stripped:
            in_package = False
            in_deps = False
            continue
        if in_package and "=" in stripped:
            key, val = stripped.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in ("name", "version", "description"):
                info[key] = val
        if in_deps and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key:
                info["dependencies"].append(key)

    info["dependencies"] = info["dependencies"][:25]
    return info


def extract_stack_info(fname: str, content: str, stack_type: str) -> dict:
    """从技术栈文件提取关键信息(不读全部,只摘关键)"""
    info = {}
    if fname == "package.json":
        try:
            pkg = json.loads(content)
            info["name"] = pkg.get("name", "")
            info["version"] = pkg.get("version", "")
            info["description"] = pkg.get("description", "")
            deps = pkg.get("dependencies", {})
            info["dependencies"] = list(deps.keys())[:20]
            info["devDependencies"] = list(pkg.get("devDependencies", {}).keys())[:10]
            info["scripts"] = list(pkg.get("scripts", {}).keys())[:10]
        except Exception:
            info["raw_excerpt"] = content[:2000]
    elif fname in ("requirements.txt",):
        lines = [l.strip().split("#")[0].strip() for l in content.splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        info["packages"] = [l for l in lines if l][:30]
    elif fname == "pyproject.toml":
        info.update(_parse_pyproject(content))
    elif fname == "go.mod":
        info.update(_parse_go_mod(content))
    elif fname == "Cargo.toml":
        info.update(_parse_cargo(content))
    elif fname in ("pom.xml", "build.gradle", "build.gradle.kts"):
        info["raw_excerpt"] = content[:2000]
    else:
        info["raw_excerpt"] = content[:2000]
    return info


def find_readme(root: Path) -> str:
    """找 README,返回截断内容"""
    for name in README_CANDIDATES:
        fpath = root / name
        if fpath.exists() and fpath.is_file():
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            return truncate(content, MAX_FILE_SIZE)
    return ""


def find_entry(root: Path, stack: dict) -> list:
    """找主入口文件,按栈类型每种取第一个找到的"""
    entries = []
    for stack_type in stack.keys():
        candidates = ENTRY_CANDIDATES.get(stack_type, [])
        for c in candidates:
            fpath = root / c
            if fpath.exists() and fpath.is_file():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                entries.append({
                    "stack": stack_type,
                    "file": c,
                    "content_excerpt": truncate(content, MAX_FILE_SIZE // 2),
                })
                break
    return entries


def find_arch(root: Path) -> list:
    """找架构文档"""
    archs = []
    for name in ARCH_CANDIDATES:
        fpath = root / name
        if fpath.exists() and fpath.is_file():
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            archs.append({"file": name, "content_excerpt": truncate(content, MAX_FILE_SIZE)})
    # 同时扫 docs/ 目录(最多 5 个)
    docs_dir = root / "docs"
    if docs_dir.exists() and docs_dir.is_dir():
        for fpath in sorted(docs_dir.iterdir()):
            if fpath.is_file() and fpath.suffix.lower() in (".md", ".rst") and len(archs) < 5:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                archs.append({
                    "file": f"docs/{fpath.name}",
                    "content_excerpt": truncate(content, MAX_FILE_SIZE // 2),
                })
    return archs


def scan_key_modules(root: Path) -> dict:
    """扫一层关键模块目录,列出文件/子目录清单(不读内容)"""
    modules = {}
    for d in KEY_DIRS:
        dpath = root / d
        if dpath.exists() and dpath.is_dir():
            try:
                files = sorted([f.name for f in dpath.iterdir() if f.is_file()])[:30]
                subdirs = sorted([f.name for f in dpath.iterdir() if f.is_dir()])[:15]
                modules[d] = {"files": files, "subdirs": subdirs}
            except Exception:
                pass
    return modules


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... [truncated]"


def build_summary(root: Path) -> dict:
    """构建结构化摘要"""
    stack = detect_stack(root)
    readme = find_readme(root)
    entries = find_entry(root, stack)
    archs = find_arch(root)
    modules = scan_key_modules(root)
    return {
        "project_path": str(root),
        "project_name": root.name,
        "stack": stack,
        "readme_excerpt": readme,
        "entries": entries,
        "arch_docs": archs,
        "key_modules": modules,
    }


def print_markdown(s: dict) -> None:
    print(f"# 项目摘要: {s['project_name']}\n")
    print(f"**路径**: `{s['project_path']}`\n")

    if s["stack"]:
        print("## 技术栈")
        for stack_type, info in s["stack"].items():
            print(f"- **{stack_type}** (from `{info['file']}`)")
            for k, v in info["info"].items():
                if isinstance(v, list):
                    print(f"  - {k}: {', '.join(v[:10]) if v else '(空)'}")
                else:
                    print(f"  - {k}: {v}")
            print()
    else:
        print("## 技术栈\n(未识别到标准技术栈文件)\n")

    if s["readme_excerpt"]:
        print("## README 摘要")
        print(f"```\n{s['readme_excerpt'][:8000]}\n```\n")

    if s["entries"]:
        print("## 主入口文件")
        for e in s["entries"]:
            print(f"- [{e['stack']}] `{e['file']}`:")
            print(f"  ```\n  {e['content_excerpt'][:1500]}\n  ```\n")

    if s["arch_docs"]:
        print("## 架构文档")
        for a in s["arch_docs"]:
            print(f"- `{a['file']}`:")
            print(f"  ```\n  {a['content_excerpt'][:2000]}\n  ```\n")

    if s["key_modules"]:
        print("## 关键模块目录(一层结构)")
        for d, info in s["key_modules"].items():
            print(f"- **{d}/**: {len(info['files'])} 文件, {len(info['subdirs'])} 子目录")
            if info["files"]:
                print(f"  - 文件: {', '.join(info['files'][:10])}")
            if info["subdirs"]:
                print(f"  - 子目录: {', '.join(info['subdirs'][:8])}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="读项目核心文件,产出结构化项目摘要(README+技术栈+入口+架构+模块结构)"
    )
    parser.add_argument("project_path", help="项目根目录路径")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown",
                        help="输出格式:json 或 markdown(默认)")
    args = parser.parse_args()

    root = Path(args.project_path).resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] 项目路径无效或不是目录: {root}", file=sys.stderr)
        return 1

    summary = build_summary(root)

    if args.output == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_markdown(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
