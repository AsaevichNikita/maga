from src.app import create_app

app = create_app()
import sys
import locale

# Устанавливаем правильную локаль для русского языка
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except:
        print("⚠️  Не удалось установить русскую локаль")

# Устанавливаем кодировку по умолчанию
if sys.stdout.encoding != 'UTF-8':
    sys.stdout.reconfigure(encoding='utf-8')
if __name__ == '__main__':
    app.run(debug=True)