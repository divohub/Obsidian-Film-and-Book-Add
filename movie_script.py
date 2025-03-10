import sys
from dotenv import load_dotenv
import io
import requests
import pyperclip
import os
import re
from deep_translator import GoogleTranslator
from transliterate import translit


load_dotenv()


# Конфигурация
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH_MOVIE")  # Укажи путь к своей папке Obsidian .env
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Вставь свой API-ключ для TMDb в .env

print(TMDB_API_KEY)


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Функция для очистки названия
def clean_filename(title):
    # Удаляем все символы, кроме букв, цифр, пробелов и дефисов
    cleaned_title = re.sub(r'[^\w\s-]', '', title)
    # Заменяем пробелы на подчёркивания (опционально)
    # cleaned_title = cleaned_title.replace(" ", "_")
    return cleaned_title


# Функция для перевода на английский
def translate_to_english(text):
    try:
        translation = GoogleTranslator(source='auto', target='en').translate(text)
        return translation
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return None

# Функция для поиска фильма в TMDb
def search_tmdb(title, year=None):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=ru-RU"
    if year:
        url += f"&year={year}"
    response = requests.get(url)
    data = response.json()
    if data.get("results"):
        if year:
            for movie in data["results"]:
                release_date = movie.get("release_date", "")
                if release_date.startswith(str(year)):
                    return movie
                
        return data["results"][0]  # Возвращаем первый результат
    return None

# Функция для получения деталей фильма по ID
def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=ru-RU"
    response = requests.get(url)
    return response.json()

# Функция для получения команды фильма (режиссёры, актёры и т.д.)
def get_movie_credits(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

# Функция для проверки языка текста
def is_russian(text):
    # Проверяем, есть ли в тексте кириллица
    return any('\u0400' <= char <= '\u04FF' for char in text)

# Функция для поиска года в тексте
def extract_year(text):
    # Ищем год в формате YYYY
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    return match.group(0) if match else None

# Функция для преобразования списка в ссылки
def format_as_links(items):
    if not items:
        return ""
    # Преобразуем каждый элемент в [[Элемент]]
    return " ".join(f"[[{item}]]" for item in items)

# Функция для преобразования жанров в ссылки
def format_genres(genres):
    if not genres:
        return ""
    # Преобразуем каждый жанр в [[Жанр]]
    return " ".join(f"[[{genre['name']}]]" for genre in genres)

# Получаем текст из буфера обмена
clipboard_text = pyperclip.paste().strip()

# Извлекаем год из буфера обмена
year = extract_year(clipboard_text)

# Извлекаем название (убираем год, если он есть)
title = re.sub(r"\b(19\d{2}|20\d{2})\b", "", clipboard_text).strip()

# Проверяем, на каком языке название
if is_russian(title):
    print("🔍 Название на русском. Пробуем найти фильм по оригинальному названию...")
    data = search_tmdb(title, year)

    # Если фильм не найден, пробуем транслитерировать и поискать снова
    if not data:
        print("🔍 Фильм не найден. Пробуем транслитерировать название...")
        transliterated_title = translit(title, 'ru', reversed=True)  # Транслитерация
        print(f"Транслитерированное название: {transliterated_title}")
        data = search_tmdb(transliterated_title, year)

        # Если фильм не найден, пробуем перевести и поискать снова
        if not data:
            print("🔍 Фильм не найден. Пробуем перевести название на английский...")
            translated_title = translate_to_english(title)
            if translated_title:
                print(f"Перевод названия: {translated_title}")
                data = search_tmdb(translated_title, year)
else:
    print("🔍 Название на английском. Пробуем найти фильм...")
    data = search_tmdb(title, year)

# Если данные найдены, создаём Markdown-файл
if data:
    # Получаем детали фильма по ID
    movie_details = get_movie_details(data['id'])
    
    # Получаем команду фильма (режиссёры, актёры и т.д.)
    movie_credits = get_movie_credits(data['id'])
    
    # Извлекаем режиссёров
    directors = [crew['name'] for crew in movie_credits.get('crew', []) if crew['job'] == 'Director']
    
    # Извлекаем пять главных актёров
    top_actors = [actor['name'] for actor in movie_credits.get('cast', [])[:5]]
    
    # Извлекаем данные
    title = movie_details.get("title", "Без названия")
    year = movie_details.get("release_date", "Год неизвестен")[:4] if movie_details.get("release_date") else "Год неизвестен"
    description = movie_details.get("overview", "Описание отсутствует.")
    genres = movie_details.get("genres", [])
    poster_path = movie_details.get("poster_path", "")
    poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else ""

    # Форматируем жанры, режиссёров и актёров в ссылки
    genres_links = format_genres(genres)
    directors_links = format_as_links(directors)
    actors_links = format_as_links(top_actors)

    # Добавляем обложку, если она есть
    poster_md = f"![Постер]({poster_url})" if poster_url else ""

    md_template = f"""---
title: {title}
year: {year}
director: {", ".join(directors) if directors else "Режиссёр неизвестен"}
genre: {", ".join(genre['name'] for genre in genres) if genres else "Жанр неизвестен"}
description: {description}
type: movie
cover: {poster_url}
---

# {title}

{poster_md}

**Год:** [[{year}]]  
**Режиссёр:** {directors_links}  
**Актёры:** {actors_links}  
**Жанр:** {genres_links}  

## Описание
{description}

### References

[[Рекомендации]]
"""

    # Сохраняем файл в папке Obsidian
    file_name = f"{clean_filename(title)}.md"
    file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_template)
    
    print(f"✅ Файл {file_name} создан в папке Obsidian!")
else:
    print("❌ Ошибка: Фильм не найден. Проверь название.")