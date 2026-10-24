import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omada_v3"))
from omada_ports import PORTS, apply_ports, configured_ports


class PortTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        fixtures = {
            "jetty.properties": "# jetty\nhttp.connector.port=8088\nhttps.connector.port=8043\n",
            "netty.properties": "# 配置\ncontroller.discovery.port=27001\ncontroller.search.port=27002\n"
                                "eap.discovery.port=29810\neap.manage.port=29811\n"
                                "eap.adopt.port=29812\neap.upgrade.port=29813\n",
            "mongodb.properties": 'eap.mongod.port=27217\neap.mongod.args=--port ${eap.mongod.port} --bind_ip 127.0.0.1\n',
            "eap.properties": "eap.rmi.port = 1099\neap.language=en\n",
        }
        for name, text in fixtures.items():
            (self.directory / name).write_text(text)

    def test_all_overrides_and_restart_changes(self):
        custom = {name: str(20000 + i) for i, name in enumerate(PORTS)}
        actual = apply_ports(self.directory, custom)
        for name, (_, filename, key, _) in PORTS.items():
            self.assertIn(key + "=" + custom[name], (self.directory / filename).read_text())
            self.assertEqual(actual[name], int(custom[name]))
        self.assertIn("--bind_ip 127.0.0.1", (self.directory / "mongodb.properties").read_text())
        self.assertIn("eap.language=en", (self.directory / "eap.properties").read_text())
        self.assertIn("# 配置", (self.directory / "netty.properties").read_text(encoding="utf-8"))
        # Settings change on every restart, even when the old values weren't defaults.
        apply_ports(self.directory, {"MANAGE_HTTP_PORT": "19088"})
        self.assertIn("http.connector.port=19088", (self.directory / "jetty.properties").read_text())
        self.assertIn("https.connector.port=8043", (self.directory / "jetty.properties").read_text())

    def test_invalid_ranges_and_collisions_do_not_change_files(self):
        cases = [{"MANAGE_HTTP_PORT": value} for value in ("443", "65536", "62000", "65500", "bad", "8043")]
        cases.append({"PORT_APP_DISCOVERY": "29810"})
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        for env in cases:
            with self.subTest(env=env), self.assertRaises(ValueError):
                apply_ports(self.directory, env)
            self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def test_tcp_and_udp_can_share_a_number(self):
        result = configured_ports({"PORT_DISCOVERY": "18088"})
        self.assertEqual(result["PORT_DISCOVERY"], result["MANAGE_HTTP_PORT"])

    def test_missing_or_duplicate_upstream_key_fails_before_writes(self):
        target = self.directory / "eap.properties"
        for text in ("unknown=true\n", "eap.rmi.port=1099\neap.rmi.port=1100\n"):
            target.write_text(text)
            before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
            with self.assertRaises(ValueError):
                apply_ports(self.directory, {})
            self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def test_ingress_template_uses_custom_https_everywhere(self):
        spec = importlib.util.spec_from_file_location("ingress_setup", ROOT / "omada_v3/ingress-setup.py")
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        template = (ROOT / "omada_v3/ingress.conf").read_text()
        with patch.dict(os.environ, {}, clear=True):
            default = setup.render_config(template, 62123)
            custom = setup.render_config(template, 62123, {"MANAGE_HTTPS_PORT": "18443"})
        self.assertIn("proxy_pass https://127.0.0.1:8043;", default)
        for directive in ("proxy_pass https://", "proxy_set_header Host ",
                          "proxy_set_header Origin https://", "proxy_set_header Referer https://"):
            self.assertIn(directive + "127.0.0.1:18443", custom)
        self.assertNotIn("@@", custom)
        self.assertIn("listen 62123;", custom)


if __name__ == "__main__":
    unittest.main(verbosity=2)
