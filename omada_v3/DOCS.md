# Using Omada v3

## Configuration

Set these options on the add-on's **Configuration** tab, save, and restart.
The add-on applies them to Omada's properties on every start, so use these
options as the source of truth rather than editing ports inside Omada.

| Option | Default | Purpose |
| --- | --- | --- |
| `MANAGE_HTTP_PORT` | 18088 | HTTP management and captive portal |
| `MANAGE_HTTPS_PORT` | 8043 | HTTPS management and captive portal; ingress follows this value |
| `PORT_APP_DISCOVERY` | 27001 | Legacy controller initialization discovery (UDP) |
| `PORT_CONTROLLER_SEARCH` | 27002 | Legacy controller initialization search (TCP) |
| `PORT_DISCOVERY` | 29810 | Access-point discovery (UDP) |
| `PORT_MANAGER_V1` | 29811 | Access-point management (TCP) |
| `PORT_ADOPT_V1` | 29812 | Access-point adoption (TCP) |
| `PORT_UPGRADE_V1` | 29813 | Access-point firmware upgrades (TCP) |
| `MONGODB_PORT` | 27217 | Internal MongoDB connection, still bound to loopback |
| `RMI_PORT` | 1099 | Legacy Java RMI port property, when used by the controller |

Ports must be between 1024 and 65535. Supervisor reserves 62000–65500 for its
allocated ingress listener, so the add-on rejects that range. Two configured
listeners cannot share the same port and protocol; TCP and UDP may share a
number. Other services on the host can still cause a conflict.

**Advanced device ports:** TP-Link advises keeping 29810, 29811, and 29812
unchanged because access points expect those ports. Changing a property does
not reconfigure the devices or their discovery broadcasts. Customize device
ports only with a matching network/device configuration. Legacy initialization
ports 27001/27002 are no longer used for that check in controller 3.2.5 and
later; the settings remain in v3's properties.

Omada v3 shares management and portal ports. There are no independent
`PORTAL_HTTP_PORT`/`PORTAL_HTTPS_PORT` options, nor separate v4/v5 listeners on
8843/29814. The ingress proxy's port is allocated automatically by Supervisor
rather than selected in this form. See [TP-Link's v3 port reference](https://support.omadanetworks.com/us/document/13087/?app=deco).

Other options:

- `TZ`: IANA timezone, default `America/Chicago`.
- `PUID` / `PGID`: user and group IDs as strings, both default `"1000"`.
- `SHOW_SERVER_LOGS`: `"true"` by default.
- `SHOW_MONGODB_LOGS`: `"false"` by default.
- `SMALL_FILES`: `"false"` by default; `"true"` enables MongoDB's legacy small journal files.

## Network and ingress

The add-on uses host networking for LAN discovery, so these options change
actual Omada listeners, not Docker port mappings. Ensure the selected ports
are free and configure any inter-VLAN routing or firewall rules accordingly.

The sidebar and **Open Web UI** use Home Assistant ingress, which follows
`MANAGE_HTTPS_PORT` automatically. For direct LAN access, use
`https://HOME_ASSISTANT_LAN_IP:MANAGE_HTTPS_PORT` with your selected number.
Sign in with your Omada account in either case.

## Storage and backups

The add-on's public configuration directory is mounted directly at
`/opt/tplink/EAPController/data`. It holds the database and controller settings.
On a local installation, this directory is typically exposed as
`/addon_configs/local_omada_v3` through tools that provide access to add-on
configuration folders. The add-on uses `addon_config`, a compatibility alias
for the newer `app_config` mount type.

The upstream image manages ownership of the data directory. Do not edit live
database files. The upstream `work` and `logs` directories are container-local;
they are not backed up by this configuration and should be treated as
disposable. Export any diagnostic logs you need before reinstalling/updating.

Home Assistant backups that include this add-on use **cold** backup mode:
Supervisor stops the controller before copying its persistent storage, then
restarts it. Shutdown has a 120-second allowance for MongoDB. Also export a
backup from Omada's UI and keep a copy outside Home Assistant. Uninstalling
the add-on can remove its stored data; take a backup first.

## Moving an existing controller

Export a backup from your existing Omada 3.x controller. Stop the old controller
before starting this one, then restore the export through the new controller's
UI using a compatible backup version. Follow TP-Link's controller migration
instructions for moving managed devices; restoring a backup alone may not
change the controller address stored by devices. Avoid running two controllers
against the same devices. Do not copy a live MongoDB directory or restore a
4.x/5.x/6.x database into this add-on.

## Initial acceptance checks

1. Confirm the add-on starts without permission or MongoDB errors in its logs.
2. Sign in through ingress or the configured HTTPS port and confirm the controller version.
3. Adopt a compatible test access point and confirm discovery and management.
4. Stop and start the add-on; verify users, settings, and adopted devices remain.
5. Create a Home Assistant backup including the add-on, and test restoration
   before depending on it for your network.

If installation cannot pull `mbentley/omada-controller:3.2`, record the full
Supervisor error and host architecture. Startup, login, and sidebar ingress have been confirmed on an amd64 Home
Assistant host; device management, restore, remote access, and arm64 runtime
checks remain pending.

## Troubleshooting without host-console access

Version 3.2.17-2 streams server.log into Home Assistant's Log tab. Enable
SHOW_MONGODB_LOGS (the string "true") for live MongoDB logs too. After a failed
startup, both logs are printed automatically, regardless of the live switches.
A tail message saying a log does not yet exist is normal on the first startup.

After updating, start the add-on and open its Log tab. Copy the error lines
under "Recent diagnostic logs" when reporting startup failures. The wrapper
adds visibility; it does not by itself resolve a controller startup failure.

This version builds locally from mbentley/omada-controller:3.2. The first update
can take longer while Home Assistant downloads the base image and builds the
small wrapper. Update through the add-on store; do not uninstall, as that may
remove controller data. The controller data mount is unchanged.

If the log reports "Port 8088 is already in use", update to 3.2.17-4 and
set MANAGE_HTTP_PORT to 18088. Confirm startup logs say http.connector.port
is being changed to 18088. This changes the actual Omada listener, not a
Docker port mapping. If another Omada controller runs on the same host, stop
it before starting this add-on: device-management ports also overlap.

## Sidebar and remote access (3.2.17-5)

Update the add-on, start it, then enable **Show in sidebar** on its Info page.
The **Omada** sidebar entry and **Open Web UI** use Home Assistant ingress.
Sign in with your Omada credentials inside the panel; Home Assistant's login
protects the ingress route, but does not replace the controller account.

When away from home, open your existing remote Home Assistant URL or Companion
App, sign in, and select Omada. Home Assistant must already be remotely
reachable (for example through Home Assistant Cloud or your existing VPN).
Ingress does not create a remote connection on its own. No additional router
port forwarding for Omada is required.

The proxy uses a dynamically allocated host port, accepts only Supervisor
connections from 172.30.32.2, and rewrites Omada's root routes, redirects, and
cookie paths for ingress. The local controller's self-signed TLS certificate
is used only over loopback; the browser uses Home Assistant's connection.
Direct LAN access on the configured HTTPS port remains available. The sidebar
entry is shown only to administrators; this visibility setting is not an
additional authentication boundary.

After updating, test login/logout, navigation, settings, and uploads/downloads
both locally and over your remote Home Assistant connection. Local startup,
login, and sidebar use have been confirmed; full remote and device-operation
checks remain pending. If you see
502 briefly during controller startup, wait for Omada to finish initializing.
If it persists, check the Log tab for controller or proxy errors.
