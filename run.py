from src.app import create_app
import os
import sys
import locale

app = create_app()

# Пытаемся выставить русскую локаль
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except Exception:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except Exception:
        print("⚠️ Не удалось установить русскую локаль")

# UTF-8 для stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )