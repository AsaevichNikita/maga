import chardet
import urllib.parse

def fix_encoding(text):
    """
    Автоматически определяет и исправляет проблемы с кодировкой.
    Работает с double-encoded UTF-8, URL encoding, и другими проблемами.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Сначала пробуем URL decoding
    if '%' in text:
        try:
            decoded = urllib.parse.unquote(text)
            if decoded != text:
                print(f"🔧 URL decoded: '{text}' -> '{decoded}'")
                text = decoded
        except:
            pass
    
    # Если текст выглядит как испорченная кодировка
    if any(c in text for c in ['Ð', 'Ñ', 'Â', 'Ã', '¡', '¢']):
        try:
            # Пробуем double-encoded UTF-8 fix
            bytes_text = text.encode('latin-1')
            detected = chardet.detect(bytes_text)
            
            if detected['encoding'] == 'utf-8':
                fixed = bytes_text.decode('utf-8')
                print(f"🔧 Fixed double-encoding: '{text}' -> '{fixed}'")
                return fixed
            else:
                # Пробуем другие кодировки
                try:
                    fixed = bytes_text.decode(detected['encoding'] or 'utf-8')
                    print(f"🔧 Fixed encoding {detected['encoding']}: '{text}' -> '{fixed}'")
                    return fixed
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Encoding fix error: {e}")
    
    return text

# Тестовые функции
def test_encoding_fixer():
    """Тестируем фиксер на различных кейсах"""
    test_cases = [
        'ÐµÑÑÐ¾Ð²',  # Петров (double-encoded UTF-8)
        '%D0%9F%D0%B5%D1%82%D1%80%D0%BE%D0%B2',  # Петров (URL encoded)
        'Ð¡Ð¸Ð´Ð¾ÑÐ¾Ð²Ð°',  # Сидорова
        'Ð£ÑÐ½Ð¸Ðº',  # Учник
        'normal text',  # Нормальный текст
        None,  # Пустое значение
    ]
    
    for test in test_cases:
        result = fix_encoding(test)
        print(f"Input: '{test}' -> Output: '{result}'")