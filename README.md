# Andy's Home Assistant Add-ons

A public collection of Home Assistant add-ons maintained by
[andynbaker](https://github.com/andynbaker). This repository hosts Omada
Controller v3 and will serve as a home for future add-ons.

## Available add-ons

| Add-on | Description | Status | Architectures |
| --- | --- | --- | --- |
| [Omada Controller v3](omada_v3/DOCS.md) | Legacy TP-Link Omada 3.2.17 controller using `mbentley/omada-controller:3.2`. | Experimental; runtime testing pending | amd64, aarch64 |

Omada v3 uses archived software that may contain unpatched vulnerabilities.
Keep its interfaces on a trusted LAN. See its
[documentation](omada_v3/DOCS.md) for configuration, storage, backups, migration,
and initial acceptance checks.

## Add this repository to Home Assistant

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fandynbaker%2Fhome-assistant-omada-v3)

Or add it manually:

1. Open **Settings → Apps → Install app** (or the **Add-on Store**).
2. Open the top-right menu and choose **Repositories**.
3. Add `https://github.com/andynbaker/home-assistant-omada-v3`.
4. Select the add-on you want, read its documentation, and install it.
5. Review its options, start it, and complete any add-on-specific setup.

A Home Assistant installation with Supervisor is required. Home Assistant
Container installations without Supervisor cannot install add-ons.

The repository URL currently retains the name of its first add-on. All future
add-ons will be available through this same URL.

## Local installation

For development or a local installation, copy the desired add-on folder into
`/addons` on your Home Assistant host. For example, Omada should be at
`/addons/omada_v3/config.yaml`. This is the local add-ons directory, not a
folder inside Home Assistant's configuration directory.

Refresh the add-on store using **Check for updates**, find the add-on under
local add-ons, and install it. Follow its documentation for setup and testing.

## Repository layout

Each add-on has its own folder and a unique `slug` in its `config.yaml`.
Shared repository metadata lives in `repository.yaml`.

```text
repository.yaml
README.md
omada_v3/
  config.yaml
  DOCS.md
```

Future add-ons will be added as sibling folders. Each add-on documents its own
requirements, supported architectures, configuration, and validation status.

Keep the repository URL stable after users install from it. Home Assistant
derives the repository ID from the URL, so renaming or moving it makes its
add-ons appear as different installations.

## Support and contributions

Use [GitHub Issues](https://github.com/andynbaker/home-assistant-omada-v3/issues)
to report problems or suggest future add-ons. Include the add-on name,
Home Assistant version, host architecture, and relevant logs with credentials
and other private information removed.

Add-ons should be tested for startup, normal operation, persistence across
restarts, and backup restoration before being relied on. Check each add-on's
documentation for remaining validation work.

## Omada implementation notes

The Omada add-on runs the upstream container directly. Its `version: "3.2"`
matches the upstream Docker tag because Supervisor pulls `image:version`.
Its entrypoint and command come from that image, and string options are passed
as environment variables through `legacy: true`.

Runtime testing on a Home Assistant host remains outstanding.

## References

- [Home Assistant repository guide](https://contributors.home-assistant.io/apps/guides/repository/)
- [Home Assistant app configuration](https://contributors.home-assistant.io/apps/reference/configuration/)
- [mbentley's archived Omada v3/v4 documentation](https://github.com/mbentley/docker-omada-controller/blob/archive_v3_v4/README_v3_and_v4.md)
