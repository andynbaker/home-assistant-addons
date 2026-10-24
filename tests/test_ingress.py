"""Integration checks: NGINX_BIN=/path/to/nginx python3 tests/test_ingress.py.

Runs the actual nginx configuration against a temporary HTTPS controller mock.
Requires nginx with http_sub_module, openssl, and Python 3. No HA host required.
"""
import hashlib
import http.client
import http.server
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/hassio_ingress/test-token"
NGINX = os.environ.get("NGINX_BIN") or shutil.which("nginx")


class Controller(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "https://127.0.0.1:8043/login")
            self.end_headers()
            return
        if self.path == "/upgrade":
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.end_headers()
            return
        body = b'<script src="js/app.js"></script><a href="/login">Login</a>'
        mime = "text/html"
        if self.path in ("/js/app.js", "/js/legacy.js"):
            body = b'var urls={normal:"/web/v1/controller",login:"/api/user/login"};var regex=/a/g;'
            mime = "application/javascript"
            if self.path == "/js/legacy.js":
                mime = "application/x-javascript"
        if self.path == "/download":
            body = bytes(range(256))
            mime = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", "JSESSIONID=test; Path=/; HttpOnly; Secure")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        result = json.dumps({"sha256": hashlib.sha256(body).hexdigest(),
                             "host": self.headers["Host"],
                             "origin": self.headers["Origin"]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)


@unittest.skipUnless(NGINX and shutil.which("openssl"), "nginx and openssl required")
class IngressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(p / "key"), "-out", str(p / "cert"),
                        "-subj", "/CN=localhost", "-days", "1"],
                       check=True, capture_output=True)
        cls.backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Controller)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(p / "cert", p / "key")
        cls.backend.socket = ctx.wrap_socket(cls.backend.socket, server_side=True)
        threading.Thread(target=cls.backend.serve_forever, daemon=True).start()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        conf = (ROOT / "omada_v3/ingress.conf").read_text()
        conf = conf.replace("@@INGRESS_PORT@@", str(cls.port))
        conf = conf.replace("https://127.0.0.1:8043;",
                            "https://127.0.0.1:%s;" % cls.backend.server_port, 1)
        conf = conf.replace("allow 172.30.32.2;", "allow 127.0.0.1;")
        conf = conf.replace("include /etc/nginx/mime.types;", "types { text/html html; }")
        conf = conf.replace("/run/omada-nginx.pid", str(p / "nginx.pid"))
        for name in ("client", "proxy"):
            conf = conf.replace("/tmp/omada-nginx-" + name, str(p / name))
        conf = conf.replace("http {", "http {\n" + "\n".join(
            "%s_temp_path %s;" % (name, p / name)
            for name in ("fastcgi", "uwsgi", "scgi")))
        (p / "nginx.conf").write_text(conf)
        cmd = [NGINX, "-p", str(p) + "/", "-c", str(p / "nginx.conf")]
        subprocess.run(cmd + ["-t"], check=True, capture_output=True)
        cls.proxy = subprocess.Popen(cmd + ["-g", "daemon off;"], stderr=subprocess.PIPE)
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=.1):
                    break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError("test proxy failed to start")

    @classmethod
    def tearDownClass(cls):
        cls.proxy.terminate()
        cls.proxy.communicate(timeout=5)
        cls.backend.shutdown()
        cls.backend.server_close()
        cls.tmp.cleanup()

    def request(self, path, method="GET", body=None, headers=None, source="127.0.0.1"):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5,
                                                 source_address=(source, 0))
        connection.request(method, path, body=body, headers=headers or {"X-Ingress-Path": PREFIX})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_redirect_cookie_and_iframe(self):
        status, headers, _ = self.request("/")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], PREFIX + "/login")
        status, headers, body = self.request("/login")
        self.assertEqual(status, 200)
        self.assertIn((PREFIX + "/login").encode(), body)
        self.assertIn("Path=" + PREFIX + "/", headers["Set-Cookie"])
        self.assertEqual(headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertIn(b'src="js/app.js"', body)

    def test_api_routes_without_damaging_javascript(self):
        status, _, body = self.request("/js/app.js")
        self.assertEqual(status, 200)
        self.assertIn((PREFIX + "/api/user/login").encode(), body)
        self.assertIn((PREFIX + "/web/v1/controller").encode(), body)
        self.assertIn(b"regex=/a/g", body)

    def test_upload_download_and_upgrade(self):
        payload = bytes(range(256)) * 4096
        status, _, body = self.request("/upload", "POST", payload)
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["host"], "127.0.0.1:8043")
        self.assertEqual(result["origin"], "https://127.0.0.1:8043")
        self.assertEqual(self.request("/download")[2], bytes(range(256)))
        headers = {"X-Ingress-Path": PREFIX, "Upgrade": "websocket", "Connection": "Upgrade"}
        self.assertEqual(self.request("/upgrade", headers=headers)[0], 101)

    def test_legacy_omada_javascript_mime_type(self):
        status, headers, body = self.request("/js/legacy.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/x-javascript")
        self.assertIn((PREFIX + "/web/v1/controller").encode(), body)
        self.assertIn((PREFIX + "/api/user/login").encode(), body)

    def test_access_restrictions_and_path_normalization(self):
        self.assertEqual(self.request("/login", source="127.0.0.2")[0], 403)
        self.assertEqual(self.request("/login", headers={"X-Ingress-Path": "/bad"})[0], 403)
        self.assertEqual(self.request("/login", headers={"Other": "missing path"})[0], 403)
        body = self.request("/login", headers={"X-Ingress-Path": PREFIX + "/"})[2]
        self.assertIn((PREFIX + "/login").encode(), body)
        self.assertNotIn((PREFIX + "//login").encode(), body)


class SetupTests(unittest.TestCase):
    def test_allocated_port_validation(self):
        spec = importlib.util.spec_from_file_location("setup", ROOT / "omada_v3/ingress-setup.py")
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        for port in (62000, 65500, 8099, True, "62000"):
            with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test"}), \
                 patch.object(setup.urllib.request, "urlopen") as get, \
                 patch.object(setup.time, "sleep"):
                get.return_value.__enter__.return_value.read.return_value = json.dumps(
                    {"data": {"ingress_port": port}}).encode()
                if type(port) is int and 62000 <= port <= 65500:
                    self.assertEqual(setup.ingress_port(), port)
                else:
                    with self.assertRaises(ValueError):
                        setup.ingress_port()


if __name__ == "__main__":
    unittest.main(verbosity=2)
