FROM nginx:alpine

# Copy files
COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/nginx.conf

# Permissions for OpenShift (GID 0)
RUN chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

EXPOSE 8080

# Start Nginx forcing PID to /tmp
CMD ["nginx", "-g", "daemon off; pid /tmp/nginx.pid;"]