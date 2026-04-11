# maga-ui (static UI)

## Быстрый деплой (Ubuntu + nginx)

### 1) Скопировать UI в web-root
```bash
sudo mkdir -p /var/www/maga-ui
sudo rsync -a ./maga-ui/ /var/www/maga-ui/
sudo chown -R www-data:www-data /var/www/maga-ui
```

### 2) nginx: правильный root + прокси /api/
**Рекомендуемый вариант**: UI работает через `/api/*`, а nginx режет `/api/` и проксирует в Flask.

Пример server-блока:

```nginx
server {
  listen 80;
  server_name localhost;

  root /var/www/maga-ui;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  # API: /api/* -> Flask без префикса /api
  location /api/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### 3) Перезагрузить nginx
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Если у тебя API НЕ через /api
Открой `assets/js/config.js` и поменяй:

```js
window.API_BASE = '';
```

И тогда UI будет стучаться напрямую в `/courses/`, `/assistants/` и т.д. (нужно, чтобы nginx проксировал эти location отдельно).
