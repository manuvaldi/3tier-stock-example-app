FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && \
    chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

EXPOSE 8080

# Comma-separated list: upstream uses all; proxy_next_upstream retries on failure.
# Backend port: numeric BACKEND_PORT, or on OpenShift/K8s BACKEND_PORT may be tcp://ip:port
# (injected for Service "backend") — the entrypoint extracts the port or uses BACKEND_SERVICE_PORT.
# Override any time: BACKEND_LISTEN_PORT=5000
ENV BACKEND_HOST=backend
ENV BACKEND_PORT=5000
ENV BACKEND_LISTEN_PORT=
# Optional: BACKEND_URL=http://host:port/path takes priority over BACKEND_HOST when both are set.
# Single-server upstream is built from the URL host and port (path is ignored).
ENV BACKEND_URL=
# Optional: value for response header X-Hostname (defaults to nginx $hostname if unset).
ENV HOSTEDNAME=

# Optional at startup: DNS/TCP probes per host (see docker-entrypoint.sh).
# e.g. slow DNS on K8s: BACKEND_PROBE_ATTEMPTS=30 BACKEND_PROBE_SLEEP=2
# Disable filter (risk of [emerg] if resolution fails): BACKEND_SKIP_PROBE=1

ENTRYPOINT ["/docker-entrypoint.sh"]