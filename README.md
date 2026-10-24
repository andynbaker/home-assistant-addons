# Omada Controller v3 Home Assistant add-on

Runs the existing `mbentley/omada-controller:3.2` image in Home Assistant OS
with Supervisor. Upstream identifies this tag as Omada **3.2.17** and lists
amd64 and arm64 support. Home Assistant calls arm64 `aarch64`.

This is an experimental add-on configuration, not a rebuilt controller image.
It has not yet been run on a Home Assistant host. The legacy image is archived
and may contain unpatched vulnerabilities; keep its interfaces on a trusted LAN.

## Install from the public repository

1. Open **Settings → Apps → Install app** (or the **Add-on Store**).
2. Open the top-right menu, choose **Repositories**, and add:
   `https://github.com/andynbaker/home-assistant-omada-v3`
3. Install **Omada Controller v3 (mbentley)**, review its options, and start it.
4. Choose **Open Web UI** to complete controller setup.

## Future add-ons

This repository can host additional add-ons. Give each add-on its own folder
and a unique slug in its `config.yaml`, alongside `omada_v3`. Keep the repository
URL stable after installation: changing it changes Home Assistant's repository
ID and makes its add-ons appear as different installations.

## Local installation

You can also install locally using the steps below.

1. Copy the entire `omada_v3` folder into `/addons` on your Home Assistant host,
   giving `/addons/omada_v3/config.yaml`. This is the local add-ons directory,
   not the `addons` directory inside Home Assistant's configuration folder.
2. Open **Settings → Apps** (called **Add-ons** on older installations), open
   the store, and choose **Check for updates** from its menu.
3. Find **Omada Controller v3 (mbentley)** under local add-ons and install it.
4. Review its configuration and start it. Installation pulls the upstream image;
   no Docker build is needed. Allow several minutes for first startup.
5. Choose **Open Web UI**, or visit `https://HOME_ASSISTANT_LAN_IP:8043`.
   An initial self-signed certificate warning is expected.
6. Complete the Omada setup wizard and then enable **Start on boot** if wanted.

See [the add-on documentation](omada_v3/DOCS.md) for storage, migration, and
troubleshooting. Home Assistant Container installations without Supervisor
cannot install add-ons.

## Design and validation

The Supervisor pulls `image:version`, so `version: "3.2"` deliberately matches
the upstream tag. Do not change this to an add-on release number such as `1.0.0`.
The controller's entrypoint and command come directly from the upstream image.
String options are forwarded as environment variables through `legacy: true`.
The add-on requests neither Supervisor API access nor privileged host access.

Before relying on it, verify on your Home Assistant host: installation and
startup, device discovery/adoption, stop/start persistence, and a full backup
and restore. There is no Docker executable or Home Assistant Supervisor in
the development workspace, so those runtime checks remain outstanding.

References:
- [mbentley's archived v3/v4 documentation](https://github.com/mbentley/docker-omada-controller/blob/archive_v3_v4/README_v3_and_v4.md)
- [Home Assistant app configuration](https://contributors.home-assistant.io/apps/reference/configuration/)
