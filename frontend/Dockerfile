FROM nginx:alpine

# Copiamos el HTML
COPY index.html /usr/share/nginx/html/index.html

# Ajustamos permisos y rutas para que Nginx funcione sin ser ROOT
# 1. Cambiamos el puerto a 8080
# 2. Movemos las rutas de archivos temporales a /tmp
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf && \
    sed -i '/user  nginx;/d' /etc/nginx/nginx.conf && \
    sed -i 's|/var/run/nginx.pid|/tmp/nginx.pid|g' /etc/nginx/nginx.conf && \
    sed -i '/http {/a \    proxy_temp_path /tmp/proxy_temp;\n    client_body_temp_path /tmp/client_body_temp;\n    fastcgi_temp_path /tmp/fastcgi_temp;\n    uwsgi_temp_path /tmp/uwsgi_temp;\n    scgi_temp_path /tmp/scgi_temp;' /etc/nginx/nginx.conf && \
    chown -R 1001:0 /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R 775 /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx

# OpenShift usará un usuario aleatorio, pero pertenecerá al grupo root (0)
USER 1001

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]