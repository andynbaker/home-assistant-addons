#!/usr/bin/python3
"""Get Supervisor's allocated ingress port and render the local proxy config."""
import json
import os
import time
import urllib.request
from pathlib import Path
from omada_ports import configured_ports

def ingress_port():
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise RuntimeError("SUPERVISOR_TOKEN is missing; ingress requires Supervisor")
    request = urllib.request.Request(
        "http://supervisor/addons/self/info",
        headers={"Authorization": "Bearer " + token},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                info = json.load(response)
            port = info["data"]["ingress_port"]
            if isinstance(port, bool) or not isinstance(port, int) or not 62000 <= port <= 65500:
                raise ValueError("Supervisor returned an invalid allocated ingress port")
            return port
        except (OSError, ValueError, KeyError):
            if attempt == 4:
                raise
            time.sleep(1)

def render_config(template, port, environment=None):
    ports = configured_ports(environment)
    return template.replace("@@INGRESS_PORT@@", str(port)).replace(
        "@@MANAGE_HTTPS_PORT@@", str(ports["MANAGE_HTTPS_PORT"]))


def main():
    port = ingress_port()
    template = Path("/etc/omada-ingress.conf.template").read_text()
    Path("/run/omada-ingress.conf").write_text(
        render_config(template, port)
    )
    print("INFO: Home Assistant ingress proxy uses port " + str(port), flush=True)

if __name__ == "__main__":
    main()
