"""Version synchronization and failure behavior on isolated manifests."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github/scripts/version.py"
spec = importlib.util.spec_from_file_location("plugin_version", SCRIPT)
assert spec is not None and spec.loader is not None
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)


class VersionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "VERSION").write_text("0.4.0\n", encoding="utf-8")
        self.paths = [self.root / name for name in version.MANIFESTS]
        for path in self.paths:
            path.parent.mkdir()
            path.write_text('{"version": "0.3.1", "name": "agentfleex"}\n', encoding="utf-8")

    def test_sync_and_check(self) -> None:
        original = [path.read_bytes() for path in self.paths]
        with self.assertRaisesRegex(ValueError, "run python"):
            version.sync(self.root, check=True)
        self.assertEqual(original, [path.read_bytes() for path in self.paths])
        version.sync(self.root, check=False)
        for path in self.paths:
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"version": "0.4.0", "name": "agentfleex"},
            )
        version.sync(self.root, check=True)

    def test_invalid_version_does_not_write(self) -> None:
        original = [path.read_bytes() for path in self.paths]
        (self.root / "VERSION").write_text("invalid\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "VERSION"):
            version.sync(self.root, check=False)
        self.assertEqual(original, [path.read_bytes() for path in self.paths])

    def test_invalid_manifest_does_not_partially_write(self) -> None:
        original = self.paths[0].read_bytes()
        self.paths[1].write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "string version"):
            version.sync(self.root, check=False)
        self.assertEqual(original, self.paths[0].read_bytes())


if __name__ == "__main__":
    unittest.main()
