#!/usr/bin/python3
"""Apply Omada v3's actual port properties before the upstream entrypoint."""
import os
from pathlib import Path
import re

# option: (default, properties file, property key, transport)
PORTS = {
    "MANAGE_HTTP_PORT": (18088, "jetty.properties", "http.connector.port", "tcp"),
    "MANAGE_HTTPS_PORT": (8043, "jetty.properties", "https.connector.port", "tcp"),
    "PORT_APP_DISCOVERY": (27001, "netty.properties", "controller.discovery.port", "udp"),
    "PORT_CONTROLLER_SEARCH": (27002, "netty.properties", "controller.search.port", "tcp"),
    "PORT_DISCOVERY": (29810, "netty.properties", "eap.discovery.port", "udp"),
    "PORT_MANAGER_V1": (29811, "netty.properties", "eap.manage.port", "tcp"),
    "PORT_ADOPT_V1": (29812, "netty.properties", "eap.adopt.port", "tcp"),
    "PORT_UPGRADE_V1": (29813, "netty.properties", "eap.upgrade.port", "tcp"),
    "MONGODB_PORT": (27217, "mongodb.properties", "eap.mongod.port", "tcp"),
    "RMI_PORT": (1099, "eap.properties", "eap.rmi.port", "tcp"),
}


def configured_ports(environment=None):
    environment = os.environ if environment is None else environment
    ports = {}
    listeners = {}
    for name, (default, _file, _key, protocol) in PORTS.items():
        raw = str(environment.get(name, default))
        if not re.fullmatch(r"[0-9]+", raw):
            raise ValueError(name + " must be an integer")
        port = int(raw)
        if not 1024 <= port <= 65535:
            raise ValueError(name + " must be between 1024 and 65535")
        if 62000 <= port <= 65500:
            raise ValueError(name + " conflicts with Supervisor's reserved ingress range 62000-65500")
        listener = (protocol, port)
        if listener in listeners:
            raise ValueError(name + " conflicts with " + listeners[listener] + " on " + protocol + "/" + str(port))
        listeners[listener] = name
        ports[name] = port
    return ports


def apply_ports(directory, environment=None):
    ports = configured_ports(environment)
    contents = {}
    for name, (_default, filename, key, _protocol) in PORTS.items():
        path = directory / filename
        text = contents.get(path)
        if text is None:
            text = path.read_text()
        pattern = r"(?m)^[ \t]*" + re.escape(key) + r"[ \t]*=.*$"
        text, count = re.subn(pattern, key + "=" + str(ports[name]), text)
        if count != 1:
            raise ValueError("Expected exactly one " + key + " in " + filename)
        contents[path] = text
    # Validate all files before changing any. Never touch the controller database.
    for path, text in contents.items():
        path.write_text(text)
    return ports


def main():
    ports = apply_ports(Path("/opt/tplink/EAPController/properties"))
    for name, value in ports.items():
        print("INFO: " + name + "=" + str(value), flush=True)


if __name__ == "__main__":
    main()
