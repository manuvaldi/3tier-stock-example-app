FROM nginx:alpine

# 1. Copiamos el HTML
COPY index.html /usr/share/nginx/html/index.html

# 2. Limpieza total de rutas y puertos para OpenShift
RUN # Cambiamos puerto 80 a 8080 \
    sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf && \
    # ELIMINAMOS la línea del PID original para evitar el error de duplicado \
    sed -i '/pid/d' /etc/nginx/nginx.conf && \
    # Ajustamos permisos de carpetas para el grupo root (GID 0) \
    chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

# Puerto no privilegiado
EXPOSE 8080

# 3. Arrancamos definiendo el PID en una zona segura (/tmp)
CMD ["nginx", "-g", "daemon off; pid /tmp/nginx.pid;"]