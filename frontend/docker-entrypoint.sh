#!/bin/sh
set -e

PORT="${BACKEND_PORT:-5000}"
UPSTREAM_FILE="${NGINX_UPSTREAM_FILE:-/tmp/nginx-upstream.conf}"
TEMPLATE="${NGINX_TEMPLATE:-/etc/nginx/templates/nginx.conf.template}"
OUT_CONF="${NGINX_CONF:-/etc/nginx/nginx.conf}"

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
            echo "    server ${h}:${PORT} max_fails=2 fail_timeout=10s;"
            _count=$((_count + 1))
        done
        IFS="$_old_ifs"
        if [ "$_count" -eq 0 ]; then
            echo "    server backend:${PORT} max_fails=2 fail_timeout=10s;"
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

    {
        echo "upstream backends {"
        echo "    server ${host}:${srv_port} max_fails=2 fail_timeout=10s;"
        echo "}"
    } >"$UPSTREAM_FILE"
}

if [ -n "${BACKEND_HOST:-}" ]; then
    write_upstream_from_hosts
elif [ -n "${BACKEND_URL:-}" ]; then
    write_upstream_from_url
else
    {
        echo "upstream backends {"
        echo "    server backend:${PORT} max_fails=2 fail_timeout=10s;"
        echo "}"
    } >"$UPSTREAM_FILE"
fi

cp "$TEMPLATE" "$OUT_CONF"
exec nginx -g "daemon off; pid /tmp/nginx.pid;"
