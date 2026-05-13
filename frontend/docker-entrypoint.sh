#!/bin/sh
set -e

# BACKEND_PORT is often plain "5000", but Kubernetes/OpenShift injects
# BACKEND_PORT=tcp://<ip>:<port> for a Service named "backend", which nginx rejects.
# Optional BACKEND_LISTEN_PORT overrides everything (use if you need a fixed port name).
# If BACKEND_PORT is not a positive integer, fall back to BACKEND_SERVICE_PORT then 5000.
resolve_backend_port() {
    if [ -n "${BACKEND_LISTEN_PORT:-}" ]; then
        printf '%s' "$BACKEND_LISTEN_PORT"
        return
    fi
    _bp="${BACKEND_PORT:-}"
    case "$_bp" in
        *://*)
            printf '%s' "$_bp" | sed 's/.*://'
            return
            ;;
    esac
    case "$_bp" in
        ''|*[!0-9]*)
            printf '%s' "${BACKEND_SERVICE_PORT:-5000}"
            ;;
        *)
            printf '%s' "$_bp"
            ;;
    esac
}

PORT="$(resolve_backend_port)"
case "$PORT" in ''|*[!0-9]*) PORT=5000 ;; esac

UPSTREAM_FILE="${NGINX_UPSTREAM_FILE:-/tmp/nginx-upstream.conf}"
TEMPLATE="${NGINX_TEMPLATE:-/etc/nginx/templates/nginx.conf.template}"
OUT_CONF="${NGINX_CONF:-/etc/nginx/nginx.conf}"

# Retries per host before dropping it (useful if K8s DNS takes a few seconds).
BACKEND_PROBE_ATTEMPTS="${BACKEND_PROBE_ATTEMPTS:-1}"
BACKEND_PROBE_SLEEP="${BACKEND_PROBE_SLEEP:-1}"
# If 1, TCP to the port (nc) is probed in addition to DNS. Useful when ICMP is blocked but the service already responds.
BACKEND_PROBE_TCP="${BACKEND_PROBE_TCP:-0}"
# If 1, hosts are not filtered (previous behavior; nginx may fail to start if resolution fails).
BACKEND_SKIP_PROBE="${BACKEND_SKIP_PROBE:-0}"

case "${BACKEND_PROBE_ATTEMPTS}" in
    ''|*[!0-9]*) BACKEND_PROBE_ATTEMPTS=1 ;;
esac
[ "$BACKEND_PROBE_ATTEMPTS" -lt 1 ] && BACKEND_PROBE_ATTEMPTS=1

case "${BACKEND_PROBE_SLEEP}" in
    ''|*[!0-9]*) BACKEND_PROBE_SLEEP=1 ;;
esac
[ "$BACKEND_PROBE_SLEEP" -lt 0 ] && BACKEND_PROBE_SLEEP=0

dns_probe() {
    _h="$1"
    if command -v getent >/dev/null 2>&1; then
        if getent ahosts "$_h" 2>/dev/null | head -n1 | grep -qE '[0-9A-Za-f:.]+'; then
            return 0
        fi
    fi
    if ping -c1 -W2 "$_h" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

tcp_probe() {
    _h="$1"
    _p="$2"
    if ! command -v nc >/dev/null 2>&1; then
        return 1
    fi
    nc -z -w3 "$_h" "$_p" >/dev/null 2>&1
}

host_passes_probe() {
    _h="$1"
    _p="$2"
    if [ "${BACKEND_SKIP_PROBE}" = "1" ]; then
        return 0
    fi
    _i=1
    while [ "$_i" -le "$BACKEND_PROBE_ATTEMPTS" ]; do
        if dns_probe "$_h"; then
            return 0
        fi
        if [ "${BACKEND_PROBE_TCP}" = "1" ] && tcp_probe "$_h" "$_p"; then
            return 0
        fi
        if [ "$_i" -lt "$BACKEND_PROBE_ATTEMPTS" ]; then
            sleep "$BACKEND_PROBE_SLEEP"
        fi
        _i=$((_i + 1))
    done
    return 1
}

emit_server_line() {
    _h="$1"
    _p="$2"
    echo "    server ${_h}:${_p} max_fails=2 fail_timeout=10s;"
}

write_upstream_from_hosts() {
    _tmp="${UPSTREAM_FILE}.new"
    {
        echo "upstream backends {"
        _old_ifs="$IFS"
        IFS=','
        _count=0
        for h in $BACKEND_HOST; do
            h=$(printf '%s' "$h" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            [ -z "$h" ] && continue
            if host_passes_probe "$h" "$PORT"; then
                emit_server_line "$h" "$PORT"
                _count=$((_count + 1))
            else
                echo "frontend(entrypoint): skipping upstream (DNS/TCP probe failed): ${h}:${PORT}" >&2
            fi
        done
        IFS="$_old_ifs"
        if [ "$_count" -eq 0 ]; then
            echo "frontend(entrypoint): warning: no host passed the probe; using placeholder so nginx can start (502 until backends are available)." >&2
            echo "    server 127.0.0.1:9;"
        fi
        echo "}"
    } >"$_tmp"
    mv "$_tmp" "$UPSTREAM_FILE"
}

write_upstream_from_url() {
    rest="$BACKEND_URL"
    rest="${rest#http://}"
    rest="${rest#https://}"
    hostport="${rest%%/*}"

    host="${hostport%%:*}"
    if [ "$host" = "$hostport" ]; then
        srv_port="$PORT"
    else
        srv_port="${hostport#*:}"
    fi

    _tmp="${UPSTREAM_FILE}.new"
    {
        echo "upstream backends {"
        if host_passes_probe "$host" "$srv_port"; then
            emit_server_line "$host" "$srv_port"
        else
            echo "frontend(entrypoint): skipping upstream from BACKEND_URL (probe failed): ${host}:${srv_port}" >&2
            echo "frontend(entrypoint): warning: using placeholder 127.0.0.1:9 so nginx can start." >&2
            echo "    server 127.0.0.1:9;"
        fi
        echo "}"
    } >"$_tmp"
    mv "$_tmp" "$UPSTREAM_FILE"
}

write_upstream_default() {
    _tmp="${UPSTREAM_FILE}.new"
    {
        echo "upstream backends {"
        if host_passes_probe "backend" "$PORT"; then
            emit_server_line "backend" "$PORT"
        else
            echo "frontend(entrypoint): warning: host 'backend' did not pass the probe; using placeholder 127.0.0.1:9." >&2
            echo "    server 127.0.0.1:9;"
        fi
        echo "}"
    } >"$_tmp"
    mv "$_tmp" "$UPSTREAM_FILE"
}

if [ -n "${BACKEND_HOST:-}" ]; then
    write_upstream_from_hosts
elif [ -n "${BACKEND_URL:-}" ]; then
    write_upstream_from_url
else
    write_upstream_default
fi

# Bake X-Hostname from HOSTEDNAME (nginx cannot read shell env); empty => nginx $hostname.
_tmp_nginx="${OUT_CONF}.new"
export HOSTEDNAME
awk '
function esc(s,    r, i, c) {
    r = ""
    for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == "\\") r = r "\\\\"
        else if (c == "\"") r = r "\\\""
        else r = r c
    }
    return r
}
{
    if (index($0, "___X_HOSTNAME___") > 0) {
        if (length(ENVIRON["HOSTEDNAME"]) == 0) {
            gsub(/___X_HOSTNAME___/, "$hostname")
        } else {
            gsub(/___X_HOSTNAME___/, "\"" esc(ENVIRON["HOSTEDNAME"]) "\"")
        }
    }
    print
}' "$TEMPLATE" >"$_tmp_nginx"
mv "$_tmp_nginx" "$OUT_CONF"

exec nginx -g "daemon off; pid /tmp/nginx.pid;"
