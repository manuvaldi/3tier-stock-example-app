FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && \
    chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

EXPOSE 8080

# Lista separada por comas: el upstream usa todos; proxy_next_upstream reintenta si falla.
# Puerto común de los backends (mismo para todos los hosts de la lista).
ENV BACKEND_HOST=backend
ENV BACKEND_PORT=5000
# Opcional (compat): si BACKEND_HOST está vacío y defines BACKEND_URL=http://host:puerto/ruta
# se genera un upstream de un solo server a partir del host y el puerto de la URL.
ENV BACKEND_URL=

ENTRYPOINT ["/docker-entrypoint.sh"]