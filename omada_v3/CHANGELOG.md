# Changelog

## 3.2.17-8

- Expose all ten port properties available in Omada v3, retaining existing defaults.
- Apply port settings directly to the controller properties before startup.
- Make ingress follow the configured HTTPS management port.
- Validate port ranges and collisions, and reserve Supervisor's dynamic ingress range.
- Document shared v3 portal ports and advanced device-port compatibility limits.

## 3.2.17-7

- Fetch fresh upstream response bodies rather than reusing a 304 response for cached, unrewritten JavaScript.
- Add a regression test for browser cache-validation headers.

## 3.2.17-6

- Fix blank ingress pages by rewriting Omada's application/x-javascript responses.
- Add a regression test using the JavaScript content type confirmed on a live controller.
- Refresh the reviewed Omada 3.2 upstream image/source baseline.
- Pin the multi-architecture image to `sha256:6239a0408deeef32c18b0d872d887eb9d3a4c6291275bfb46db755a1fb7b5f74`.
- Keep the controller on the legacy 3.2 series.

## 3.2.17-5

- Add Home Assistant ingress and an administrator-only Omada sidebar panel.
- Proxy the v3 UI with root-route, redirect, cookie, and WebSocket handling.
- Use a Supervisor-allocated port and restrict access to Supervisor.
- Keep Omada login, existing data storage, and direct LAN access on 8043.

## 3.2.17-4

- Make the HTTP management port configurable, defaulting to 18088.
- Avoid the confirmed conflict on port 8088; keep HTTPS on 8043.

## 3.2.17-3

- Restore the upstream Java CMD explicitly after overriding ENTRYPOINT.
- Fix the logging wrapper exiting with gosu usage instead of launching Omada.

## 3.2.17-2

- Stream server logs into Home Assistant's Log tab.
- Print the last server and MongoDB log lines after a failed startup.
- Build a thin wrapper around the same upstream Omada 3.2 image.
- Preserve the existing controller data mount and forward shutdown signals.
