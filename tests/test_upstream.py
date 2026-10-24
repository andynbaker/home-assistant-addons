import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("upstream", ROOT / "scripts/check_omada_upstream.py")
UPSTREAM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPSTREAM)


class UpstreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "omada_v3").mkdir()
        self.state = {"image": UPSTREAM.IMAGE, "source_repository": UPSTREAM.UPSTREAM,
                      "digest": "sha256:" + "a" * 64, "archived_source_ref": "archive_v3_v4",
                      "archived_source_commit": "b" * 40, "legacy_readme_blob": "c" * 40}
        (self.root / "omada_v3/Dockerfile").write_text("FROM " + UPSTREAM.IMAGE + "\nCMD [\"java\"]\n")
        (self.root / "omada_v3/config.yaml").write_text('version: "3.2.17-5"\nslug: omada_v3\n')
        (self.root / "omada_v3/CHANGELOG.md").write_text("# Changelog\n\n## 3.2.17-5\n\n- Existing entry.\n")

    def test_updates_pin_version_and_changelog_once(self):
        self.assertTrue(UPSTREAM.apply_update(self.root, self.state))
        self.assertIn('version: "3.2.17-6"', (self.root / "omada_v3/config.yaml").read_text())
        dockerfile = (self.root / "omada_v3/Dockerfile").read_text()
        self.assertIn("3.2@sha256:" + "a" * 64, dockerfile)
        self.assertIn('CMD ["java"]', dockerfile)
        self.assertIn("Existing entry", (self.root / "omada_v3/CHANGELOG.md").read_text())
        self.assertFalse(UPSTREAM.apply_update(self.root, self.state))
        self.assertTrue(UPSTREAM.apply_update(self.root, dict(self.state, digest="sha256:" + "d" * 64)))
        self.assertIn('version: "3.2.17-7"', (self.root / "omada_v3/config.yaml").read_text())

    def test_source_change_creates_reviewable_update(self):
        UPSTREAM.apply_update(self.root, self.state)
        self.assertTrue(UPSTREAM.apply_update(self.root, dict(self.state, legacy_readme_blob="e" * 40)))

    def test_never_changes_controller_series(self):
        with self.assertRaises(ValueError):
            UPSTREAM.apply_update(self.root, dict(self.state, image="mbentley/omada-controller:latest"))
        (self.root / "omada_v3/Dockerfile").write_text("FROM mbentley/omada-controller:6\n")
        with self.assertRaises(ValueError):
            UPSTREAM.apply_update(self.root, self.state)
        self.assertEqual((self.root / "omada_v3/config.yaml").read_text(), 'version: "3.2.17-5"\nslug: omada_v3\n')

    def test_invalid_digest_leaves_files_untouched(self):
        before = (self.root / "omada_v3/Dockerfile").read_text()
        with self.assertRaises(ValueError):
            UPSTREAM.apply_update(self.root, dict(self.state, digest="malformed"))
        self.assertEqual((self.root / "omada_v3/Dockerfile").read_text(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
