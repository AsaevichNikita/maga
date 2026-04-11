FROM nginx:stable-alpine

COPY frontend/maga-ui /usr/share/nginx/html
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
