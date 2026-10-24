# Changelog

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
