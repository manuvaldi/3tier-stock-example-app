FROM nginx:alpine

# Copiamos el HTML
COPY index.html /usr/share/nginx/html/index.html

# Modificamos la configuración de Nginx para que escuche en el 8080
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf

# Exponemos formalmente el 8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]