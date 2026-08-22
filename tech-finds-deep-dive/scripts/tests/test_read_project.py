#!/usr/bin/env python3
"""read_project.py 单元测试。"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from read_project import (
    _parse_cargo,
    _parse_go_mod,
    _parse_pyproject,
    build_summary,
)


class StackParsingTests(unittest.TestCase):
    """验证各语言技术栈文件解析。"""

    def test_parse_pyproject_dependencies(self) -> None:
        content = """
[project]
name = "demo"
version = "0.1.0"
description = "A demo project"
dependencies = [
    "fastapi>=0.100.0",
    "pydantic",
    "httpx",
]
"""
        info = _parse_pyproject(content)
        self.assertEqual(info["name"], "demo")
        self.assertEqual(info["version"], "0.1.0")
        self.assertIn("fastapi>=0.100.0", info["dependencies"])
        self.assertIn("pydantic", info["dependencies"])

    def test_parse_go_mod_require_block(self) -> None:
        content = """
module github.com/demo/app

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/stretchr/testify v1.8.4 // indirect
)

require github.com/sirupsen/logrus v1.9.3
"""
        info = _parse_go_mod(content)
        self.assertEqual(info["module"], "github.com/demo/app")
        deps = info["requires"]
        self.assertIn("github.com/gin-gonic/gin", deps)
        self.assertIn("github.com/stretchr/testify", deps)
        self.assertIn("github.com/sirupsen/logrus", deps)

    def test_parse_cargo_dependencies(self) -> None:
        content = """
[package]
name = "demo"
version = "0.1.0"
description = "A Rust demo"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = "1"
"""
        info = _parse_cargo(content)
        self.assertEqual(info["name"], "demo")
        self.assertIn("serde", info["dependencies"])
        self.assertIn("tokio", info["dependencies"])


class BuildSummaryTests(unittest.TestCase):
    """验证 build_summary 端到端读取项目摘要。"""

    def test_build_summary_on_minimal_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# Demo\n\nA minimal project.", encoding="utf-8"
            )
            (root / "requirements.txt").write_text(
                "flask\nrequests>=2.0", encoding="utf-8"
            )
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")

            summary = build_summary(root)
            self.assertEqual(summary["project_name"], root.name)
            self.assertIn("python", summary["stack"])
            self.assertIn("# Demo", summary["readme_excerpt"])
            self.assertIn("src", summary["key_modules"])


if __name__ == "__main__":
    unittest.main()
