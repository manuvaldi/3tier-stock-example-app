FROM nginx:alpine

# 1. Copiamos el HTML
COPY index.html /usr/share/nginx/html/index.html

# 2. Configuramos Nginx para que sea "OpenShift Friendly"
# - Cambiamos puerto 80 a 8080
# - Ajustamos permisos para que el usuario aleatorio de OC pueda leer/escribir
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx && \
    chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx

# Exponemos el puerto no privilegiado
EXPOSE 8080

# 3. Forzamos que el PID se escriba en /tmp, donde SI hay permisos
# Esto soluciona el error: open() "/run/nginx.pid" failed
CMD ["nginx", "-g", "daemon off; pid /tmp/nginx.pid;"]