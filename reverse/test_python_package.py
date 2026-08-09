from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from bda_packer import __version__
from bda_packer import build as build_module
from bda_packer.build import bundled_prefix, sdk_include_dir


ROOT = Path(__file__).resolve().parents[1]


class PythonPackageTest(unittest.TestCase):
    def test_version_is_synchronized(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        public_header = (ROOT / "sdk/include/bda_types.h").read_text(
            encoding="utf-8"
        )

        self.assertEqual(__version__, "0.1.0a1")
        self.assertIn('version = "0.1.0a1"', pyproject)
        self.assertIn('BDA_SDK_VERSION_STRING "0.1.0-alpha.1"', public_header)

    def test_console_scripts_are_declared(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('bda-pack = "bda_packer.build:main"', pyproject)
        self.assertIn('bda-validate = "bda_packer.validate:main"', pyproject)
        self.assertIn('bda-icon = "bda_packer.vx_icon:main"', pyproject)

    def test_dual_license_metadata_and_notices_exist(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(
            'license = "Apache-2.0 OR GPL-2.0-only"', pyproject)
        self.assertIn(
            'license-files = ["LICENSE", "LICENSE-GPL-2.0", "NOTICE"]',
            pyproject,
        )
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertTrue((ROOT / "LICENSE-GPL-2.0").is_file())
        self.assertTrue((ROOT / "NOTICE").is_file())
        self.assertIn("Apache License", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn(
            "GNU GENERAL PUBLIC LICENSE",
            (ROOT / "LICENSE-GPL-2.0").read_text(encoding="utf-8"),
        )
        self.assertIn("Copyright 2026 HelloClyde", (ROOT / "NOTICE").read_text(encoding="utf-8"))

    def test_configured_sdk_include_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            include = Path(temp_dir)
            (include / "bda_sdk.h").write_text("/* test */\n", encoding="ascii")
            with patch.dict(os.environ, {"BDA_SDK_INCLUDE": str(include)}):
                self.assertEqual(sdk_include_dir(), include)

    def test_bundled_toolchain_prefers_new_cache_and_supports_legacy_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current_bin = root / ".toolchain/bin"
            legacy_bin = root / "tools/bin"
            current_bin.mkdir(parents=True)
            legacy_bin.mkdir(parents=True)
            current_gcc = current_bin / "mipsel-none-elf-gcc.exe"
            legacy_gcc = legacy_bin / "mipsel-none-elf-gcc.exe"
            current_gcc.write_bytes(b"")
            legacy_gcc.write_bytes(b"")

            with patch.object(build_module, "REPO_ROOT", root):
                self.assertEqual(
                    bundled_prefix(),
                    str(current_bin / "mipsel-none-elf-"),
                )
                current_gcc.unlink()
                self.assertEqual(
                    bundled_prefix(),
                    str(legacy_bin / "mipsel-none-elf-"),
                )

    def test_public_front_door_links_resolve(self) -> None:
        documents = [
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "SECURITY.md",
            ROOT / "CHANGELOG.md",
            ROOT / "bda_packer/README.md",
            ROOT / "docs/README.md",
            ROOT / "docs/getting_started.md",
            ROOT / "docs/compatibility.md",
            ROOT / "docs/releasing.md",
            ROOT / "example/README.md",
        ]
        pattern = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for target in pattern.findall(text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                path_text = target.strip("<>").split("#", 1)[0]
                resolved = (document.parent / path_text).resolve()
                self.assertTrue(resolved.exists(), f"{document}: missing {target}")


if __name__ == "__main__":
    unittest.main()
