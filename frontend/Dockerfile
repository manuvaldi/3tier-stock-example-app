FROM nginx:alpine

# Copy the application HTML
COPY index.html /usr/share/nginx/html/index.html

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Adjust permissions for OpenShift (GID 0)
# We make sure the random user can write to cache and logs
RUN chgrp -R 0 /var/cache/nginx /var/log/nginx /etc/nginx && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /etc/nginx

# Expose the non-privileged port
EXPOSE 8080

# Start Nginx forcing the PID to /tmp to avoid permission errors
CMD ["nginx", "-g", "daemon off; pid /tmp/nginx.pid;"]