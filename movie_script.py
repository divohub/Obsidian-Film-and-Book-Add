import sys
import io
import requests
import pyperclip
import os
import re
from deep_translator import GoogleTranslator


# Конфигурация
OBSIDIAN_VAULT_PATH = r"C:\Users\user\iCloudDrive\iCloud~md~obsidian\divo\30 - Source Material\37 Films"  # Укажи путь к своей папке Obsidian
OMDB_API_KEY = "5839c8e0"  # Вставь сюда свой API-ключ для OMDb



sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if not os.path.exists(OBSIDIAN_VAULT_PATH):
    print(f"❌ Ошибка: Путь {OBSIDIAN_VAULT_PATH} не существует.")
else:
    print(f"✅ Путь {OBSIDIAN_VAULT_PATH} найден.")



def extract_year(text):
    # Ищем год в формате YYYY
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    return match.group(0) if match else None


def translate_to_english(text):
    try:
        translation = GoogleTranslator(source='auto', target='en').translate(text)
        return translation
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return None

# Функция для поиска фильма
def search_movie(title, year=None):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    if year:
        url += f"&y={year}"
    response = requests.get(url)
    data = response.json()
    return data if data.get("Response") == "True" else None

# Функция для проверки языка текста
def is_russian(text):
    # Проверяем, есть ли в тексте кириллица
    return any('\u0400' <= char <= '\u04FF' for char in text)

# Получаем название из буфера обмена
clipboard_text = pyperclip.paste().strip()

year = extract_year(clipboard_text)

title = re.sub(r"\b(19\d{2}|20\d{2})\b", "", clipboard_text).strip()


# Функция для преобразования жанров в ссылки
def format_genres(genres):
    if not genres:
        return ""
    # Разделяем жанры по запятым и убираем лишние пробелы
    genre_list = [genre.strip() for genre in genres.split(",")]
    # Преобразуем каждый жанр в [[Жанр]]
    return " ".join(f"[[{genre}]]" for genre in genre_list)



# Проверяем, на каком языке название
if is_russian(title):
    print("🔍 Название на русском. Пробуем найти фильм по оригинальному названию...")
    data = search_movie(title, year)

    # Если фильм не найден, пробуем перевести и поискать снова
    if not data:
        print("🔍 Фильм не найден. Пробуем перевести название на английский...")
        translated_title = translate_to_english(title)
        if translated_title:
            print(f"Перевод названия: {translated_title}")
            data = search_movie(translated_title, year)
else:
    print("🔍 Название на английском. Пробуем найти фильм...")
    data = search_movie(title, year)

# Если данные найдены, создаём Markdown-файл
if data:
    # Форматируем жанры в ссылки
    genres = format_genres(data.get("Genre", ""))

      # Добавляем постер, если он есть
    poster_url = data.get("Poster", "")
    poster_md = f"![Постер]({poster_url})" if poster_url else ""

    md_template = f"""---



title: {data['Title']}
year: {data['Year']}
director: {data['Director']}
genre: {data['Genre']}
description: {data['Plot']}
type: movie
---

# {data['Title']}


{poster_md}

**Год:** [[{data['Year']}]]  
**Режиссёр:** [[{data['Director']}]]  
**Жанр:** {genres}  

## Описание
{data['Plot']}


## Refrences

[[Рекомендации]]

"""

    # Сохраняем файл в папке Obsidian
    file_name = f"{data['Title']}.md"
    file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_template)
    
    print(f"✅ Файл {file_name} создан в папке Obsidian!")
else:
    print("❌ Ошибка: Фильм не найден. Проверь название.")