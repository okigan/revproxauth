FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY config/ /etc/nginx/conf.d/

# Create cache directory for auth requests
RUN mkdir -p /var/cache/nginx/auth_cache

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
