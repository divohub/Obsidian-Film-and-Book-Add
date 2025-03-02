import requests
import pyperclip
import os
from googletrans import Translator

# Конфигурация
OBSIDIAN_VAULT_PATH = r"C:\Users\user\iCloudDrive\iCloud~md~obsidian\divo\30 - Source Material\37 Films"  # Укажи путь к своей папке Obsidian
OMDB_API_KEY = "http://www.omdbapi.com/?i=tt3896198&apikey=5839c8e0"  # Вставь сюда свой API-ключ для OMDb



if not os.path.exists(OBSIDIAN_VAULT_PATH):
    print(f"❌ Ошибка: Путь {OBSIDIAN_VAULT_PATH} не существует.")
else:
    print(f"✅ Путь {OBSIDIAN_VAULT_PATH} найден.")



# Функция для перевода на английский
def translate_to_english(text):
    try:
        translation = GoogleTranslator(source='auto', target='en').translate(text)
        return translation
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return None

# Функция для поиска фильма
def search_movie(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data if data.get("Response") == "True" else None

# Получаем название из буфера обмена
title = pyperclip.paste().strip()

# Проверяем, есть ли в названии кириллица
is_russian = any('\u0400' <= char <= '\u04FF' for char in title)

# Сначала пробуем найти фильм по оригинальному названию
data = search_movie(title)

# Если фильм не найден и название на русском, пробуем перевести и поискать снова
if not data and is_russian:
    print("🔍 Фильм не найден. Пробуем перевести название...")
    translated_title = translate_to_english(title)
    if translated_title:
        print(f"Перевод названия: {translated_title}")
        data = search_movie(translated_title)

# Если данные найдены, создаём Markdown-файл
if data:
    md_template = f"""---
title: {data['Title']}
year: {data['Year']}
director: {data['Director']}
genre: {data['Genre']}
description: {data['Plot']}
type: movie
---

# {data['Title']}

**Год:** {data['Year']}  
**Режиссёр:** {data['Director']}  
**Жанр:** {data['Genre']}  

## Описание
{data['Plot']}
"""

    # Сохраняем файл в папке Obsidian
    file_name = f"{data['Title']}.md"
    file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_template)
    
    print(f"✅ Файл {file_name} создан в папке Obsidian!")
else:
    print("❌ Ошибка: Фильм не найден. Проверь название.")