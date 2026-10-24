# Using Omada v3

## Configuration

- `MANAGE_HTTP_PORT`: HTTP management port, default `18088`. Choose an unused
  port between 1024 and 65535. HTTPS remains on 8043.
- `TZ`: IANA timezone, default `America/Chicago`.
- `PUID` and `PGID`: numeric user and group IDs, supplied as strings. Both
  default to `"1000"` to match the existing container configuration.
- `SHOW_SERVER_LOGS`: default `"true"`.
- `SHOW_MONGODB_LOGS`: default `"false"`.
- `SMALL_FILES`: choose the string `"true"` or `"false"`. Enables MongoDB's
  legacy small journal files option when true. Default is `"false"`.

Restart the add-on after changing options. The HTTP management port follows
MANAGE_HTTP_PORT. Keep HTTPS on 8043 in Omada's own UI so the Open Web UI
button continues to work.

The environment also preserves `PORTAL_HTTP_PORT=8088` and
`PORTAL_HTTPS_PORT=8843` from the existing Compose configuration. Upstream
documents that Omada 3.2 ignores these two variables; portal settings must be
managed in the controller itself. The add-on wrapper implements the logging switches; the upstream image handles
UID/GID settings.

## Network

Host networking supports LAN broadcast discovery. Ensure another controller
or service is not using TCP 18088 (or your configured HTTP management port), 8043, 8843, or 29811–29814, or UDP 29810.
The HTTP management port differs from upstream's default of 8088 to avoid a
confirmed conflict on the Home Assistant host. Omada v3 may still use 8088 for
its portal; changing the management port does not change portal settings. The add-on's network ports cannot
be remapped through Supervisor when using host networking. Across VLANs,
configure routing and discovery according to your access points' requirements.

Open Web UI uses your Home Assistant hostname. If that hostname points to a
remote proxy that only serves Home Assistant, use the host's LAN IP directly.
Omada has its own login; Home Assistant ingress is not configured.

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
2. Sign in on port 8043 and confirm the displayed controller version.
3. Adopt a compatible test access point and confirm discovery and management.
4. Stop and start the add-on; verify users, settings, and adopted devices remain.
5. Create a Home Assistant backup including the add-on, and test restoration
   before depending on it for your network.

If installation cannot pull `mbentley/omada-controller:3.2`, record the full
Supervisor error and host architecture. Upstream tag availability and actual
compatibility with current Home Assistant hosts have not been runtime verified.

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
