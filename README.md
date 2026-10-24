# Andy's Home Assistant Add-ons

Home Assistant add-ons maintained by [andynbaker](https://github.com/andynbaker).

## Add-ons

| Add-on | Description |
| --- | --- |
| [Omada Controller v3](omada_v3/DOCS.md) | TP-Link Omada 3.2.17 using mbentley's Docker image, with sidebar and ingress access. Supports amd64 and aarch64. Experimental. |

Omada v3 is archived software and may contain unpatched vulnerabilities.
Keep its ports on your trusted LAN.

## Installation

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fandynbaker%2Fhome-assistant-addons)

Or open the **Add-on Store → ⋮ → Repositories** and add:

```text
https://github.com/andynbaker/home-assistant-addons
```

Install your add-on, review its configuration, and start it. For Omada, enable
**Show in sidebar** to open it inside Home Assistant. Remote access works
through your existing remote Home Assistant connection.

Requires a Home Assistant installation with Supervisor.

## Updates and support

A daily [GitHub Action](https://github.com/andynbaker/home-assistant-addons/actions/workflows/omada-upstream.yml)
checks for upstream Omada 3.2 changes and opens a PR for review. Updates are
not merged automatically.

- [Omada setup and troubleshooting](omada_v3/DOCS.md)
- [Report an issue or suggest an add-on](https://github.com/andynbaker/home-assistant-addons/issues)
- [Maintenance and development](MAINTENANCE.md)
