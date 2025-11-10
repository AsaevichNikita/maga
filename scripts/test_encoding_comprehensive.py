# test_encoding_comprehensive.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.encoding_fixer import fix_encoding, test_encoding_fixer

if __name__ == "__main__":
    print("🧪 ТЕСТИРУЕМ ФИКСЕР КОДИРОВКИ:")
    test_encoding_fixer()
    
    # Дополнительные тесты
    test_cases = [
        'ÐµÑÑÐ¾Ð²',  # Петров
        '%D0%9F%D0%B5%D1%82%D1%80%D0%BE%D0%B2',  # URL encoded
        'Ð¡Ð¸Ð´Ð¾ÑÐ¾Ð²Ð°',  # Сидорова
        'Ð£ÑÐ½Ð¸Ðº',  # Учник
        'ÃÂ¡ÃÂ¸ÃÂ´ÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂ°',  # Тройная кодировка?
    ]
    
    for test in test_cases:
        result = fix_encoding(test)
        print(f"'{test}' -> '{result}'")