#!/bin/sh
# Keep the controller's original command; expose its file logs to Supervisor.
set -u

server_log=/opt/tplink/EAPController/logs/server.log
mongo_log=/opt/tplink/EAPController/logs/mongod.log
tail_pids=""
proxy_pid=""
stopping=false

if ! python3 /omada_ports.py; then
    echo "ERROR: Invalid or unsupported Omada port configuration."
    exit 1
fi

if [ "${SHOW_SERVER_LOGS:-true}" = "true" ]; then
    tail -n 100 -F "$server_log" &
    tail_pids="$tail_pids $!"
fi
if [ "${SHOW_MONGODB_LOGS:-false}" = "true" ]; then
    tail -n 100 -F "$mongo_log" &
    tail_pids="$tail_pids $!"
fi

# Fail visibly if the proxy cannot be configured or bind its allocated port.
if ! python3 /ingress-setup.py; then
    echo "ERROR: Could not configure Home Assistant ingress."
    for pid in $tail_pids; do kill "$pid" 2>/dev/null || true; done
    exit 1
fi
if ! nginx -t -c /run/omada-ingress.conf; then
    for pid in $tail_pids; do kill "$pid" 2>/dev/null || true; done
    exit 1
fi
nginx -c /run/omada-ingress.conf -g 'daemon off;' &
proxy_pid=$!
# Detect immediate bind/configuration failures before starting the controller.
sleep 1
if ! kill -0 "$proxy_pid" 2>/dev/null; then
    echo "ERROR: Home Assistant ingress proxy failed to start."
    for pid in $tail_pids; do kill "$pid" 2>/dev/null || true; done
    exit 1
fi

/entrypoint.sh "$@" &
controller_pid=$!

stop_controller() {
    stopping=true
    kill -TERM "$controller_pid" 2>/dev/null || true
}
trap stop_controller TERM INT

status=0
while :; do
    wait "$controller_pid"
    status=$?
    # A trapped signal can interrupt wait before the controller has exited.
    kill -0 "$controller_pid" 2>/dev/null || break
done

if [ -n "$proxy_pid" ]; then
    kill -TERM "$proxy_pid" 2>/dev/null || true
    wait "$proxy_pid" 2>/dev/null || true
fi

for pid in $tail_pids; do
    kill "$pid" 2>/dev/null || true
done
for pid in $tail_pids; do
    wait "$pid" 2>/dev/null || true
done

# A fast startup failure may happen before tail notices the new files.
if [ "$stopping" = "false" ]; then
    echo "Omada exited with status $status. Recent diagnostic logs:"
    for log in "$server_log" "$mongo_log"; do
        echo "===== $log ====="
        if [ -f "$log" ]; then
            tail -n 100 "$log"
        else
            echo "Log file was not created."
        fi
    done
fi
exit "$status"
