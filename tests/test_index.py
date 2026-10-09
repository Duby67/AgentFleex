"""Behavior of skills/fleex-index/scripts/index.py on small repositories."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills/fleex-index/scripts/index.py"
HAS_CTAGS = (
    shutil.which("ctags") is not None
    and "Universal Ctags"
    in subprocess.run(["ctags", "--version"], capture_output=True, text=True, check=False).stdout
)

FILES = {
    "store.ts": """\
        export interface User {
          id: string;
        }
        export const load = async (id: string) => {
          return fetch(id);
        };
        export default class Store {
          async get(id: string): Promise<User> {
            if (id) {
              return this.items[0];
            }
          }
        }
        """,
    "server.go": """\
        package main

        type Server struct {
        \taddr string
        }

        func (s *Server) Start() error {
        \treturn nil
        }
        """,
    "config.rs": """\
        #[derive(Debug)]
        pub struct Config {
            port: u16,
        }

        impl Config {
            pub fn new() -> Self {
                Config { port: 80 }
            }
        }
        """,
    "strings.py": '''\
        x = 'a """ inside a plain string'
        # a comment with """ in it
        class Real:
            @property
            def first(self):
                s = f"""
        class Fake:
        {x}
        """
                return s

            def second(
                self,
            ) -> None:  # noqa: D401
                add = lambda a: a
                return add
        ''',
    "deploy.sh": """\
        deploy() {
          cat <<EOF
        fake() {
        EOF
          fail()
        }

        other() { :; }
        """,
    "README.md": """\
        # Title

        ## Usage

        Text.

        ```
        # not a heading
        ```

        ## Notes
        """,
}
# Windows forbids ":" in file names; elsewhere it checks that git paths are not split on colons.
ODD_NAME = "we_ird.txt" if os.name == "nt" else "we:ird.txt"
FILES[ODD_NAME] = "uses helper\n"


class IndexTest(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory[str]
    root: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=cls.root, check=True)
        for name, text in FILES.items():
            path = cls.root / name
            # Bytes keep LF line endings on Windows too.
            path.write_bytes(textwrap.dedent(text).encode("utf-8"))
        (cls.root / "sub").mkdir()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def run_index(self, *args: str, cwd: Path | None = None) -> list[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def outline(self, name: str, backend: str) -> list[str]:
        return self.run_index("outline", name, "--backend", backend, "--limit", "999")[1:]

    def backends(self) -> list[str]:
        return ["patterns", "ctags"] if HAS_CTAGS else ["patterns"]

    def test_outline_across_languages(self) -> None:
        expected = {
            "store.ts": [
                "1-3 interface User",
                "4-6 function load",
                "7-13 class Store",
                "  8-12 method get",
            ],
            "server.go": ["3-5 struct Server", "7-9 function Start"],
            "config.rs": ["1-4 struct Config", "6-10 impl Config", "  7-9 method new"],
        }
        for backend in self.backends():
            for name, rows in expected.items():
                with self.subTest(backend=backend, file=name):
                    self.assertEqual(self.outline(name, backend), rows)

    def test_python_strings_comments_and_lambdas(self) -> None:
        rows = ["2-16 class Real", "  4-10 method first", "  12-16 method second"]
        for backend in self.backends():
            with self.subTest(backend=backend):
                self.assertEqual(self.outline("strings.py", backend), rows)

    def test_heredoc_hides_its_body(self) -> None:
        rows = ["1-6 function deploy", "  2-4 heredoc EOF", "8-8 function other"]
        for backend in self.backends():
            with self.subTest(backend=backend):
                self.assertEqual(self.outline("deploy.sh", backend), rows)

    def test_markdown_skips_fenced_headings(self) -> None:
        self.assertEqual(
            self.outline("README.md", "patterns"),
            ["1-11 h1 Title", "  3-9 h2 Usage", "  11-11 h2 Notes"],
        )

    def test_show_qualified_name_includes_decorator(self) -> None:
        lines = self.run_index("show", "strings.py", "Real.first", "--backend", "patterns")
        self.assertTrue(lines[0].startswith("strings.py:4-10"))
        self.assertEqual(lines[1].strip(), "@property")

    def test_find_and_refs_handle_colons_and_subdirectories(self) -> None:
        self.assertIn(
            "store.ts:7-13 class Store", self.run_index("find", "Store", cwd=self.root / "sub")
        )
        self.assertIn(f"{ODD_NAME}: 1 (1)", self.run_index("refs", "helper"))

    def test_map_counts_lines(self) -> None:
        self.assertIn("README.md  11 lines", self.run_index("map"))

    def test_pages_long_output(self) -> None:
        lines = self.run_index("outline", "store.ts", "--limit", "2")
        self.assertEqual(lines[-1], "... 2 more; use --offset 2")

    @unittest.skipIf(os.name == "nt", "symlinks need administrator rights on Windows")
    def test_missing_ctags_is_reported(self) -> None:
        empty = tempfile.mkdtemp()
        git = shutil.which("git")
        assert git is not None
        Path(empty, "git").symlink_to(git)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "outline", "store.ts", "--backend", "ctags"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": empty},
        )
        shutil.rmtree(empty)
        self.assertEqual(result.returncode, 1)
        self.assertIn("install Universal Ctags", result.stderr)


if __name__ == "__main__":
    unittest.main()
