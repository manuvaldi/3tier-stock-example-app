FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
# Copiamos como template
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

RUN chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

EXPOSE 8080

# Variable por defecto por si se olvida configurarla
ENV BACKEND_URL=http://backend:5000/data

# La imagen de Nginx Alpine ejecuta envsubst automáticamente sobre 
# los archivos en /etc/nginx/templates/ y los deja en /etc/nginx/conf.d/
# Pero para que sea el config PRINCIPAL, usaremos este comando:
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off; pid /tmp/nginx.pid;'"]