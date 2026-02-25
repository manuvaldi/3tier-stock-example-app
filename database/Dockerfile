FROM redis:alpine

# The default Redis directory for data
WORKDIR /data

# Adjust permissions for OpenShift (GID 0)
# This ensures that even with a random UID, Redis can write its .rdb files
RUN chgrp -R 0 /data && \
    chmod -R g+w /data

# OpenShift standard: Run as a non-root user
USER 1001

# Expose the default Redis port
EXPOSE 6379

# Start redis with a persistent save policy (optional)
CMD ["redis-server", "--protected-mode", "no"]