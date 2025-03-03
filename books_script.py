import requests
from dotenv import load_dotenv
import pyperclip
import os
from deep_translator import GoogleTranslator
import sys
import io


load_dotenv()

# Конфигурация
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH_BOOK")  # Укажи путь к своей папке Obsidian
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")  # Вставь сюда свой API-ключ для Google Books API



sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Функция для перевода на английский
def translate_to_english(text):
    try:
        translation = GoogleTranslator(source='auto', target='en').translate(text)
        return translation
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return None

# Функция для поиска книги
def search_book(title):
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&key={GOOGLE_BOOKS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("totalItems", 0) > 0:
            return data["items"][0]  # Возвращаем первую найденную книгу
    return None

# Функция для проверки языка текста
def is_russian(text):
    # Проверяем, есть ли в тексте кириллица
    return any('\u0400' <= char <= '\u04FF' for char in text)

# Функция для преобразования жанров в ссылки
def format_categories(categories):
    if not categories:
        return ""
    # Преобразуем каждый жанр в [[Жанр]]
    return " ".join(f"[[{category}]]" for category in categories)


# Функция для преобразования списка в ссылки
def format_as_links(items):
    if not items:
        return ""
    # Преобразуем каждый элемент в [[Элемент]]
    return " ".join(f"[[{item}]]" for item in items)



# Функция для сокращения описания
def shorten_description(description, max_length=500):
    if not description:
        return ""
    # Убираем лишние пробелы и сокращаем до max_length символов
    description = " ".join(description.split())
    if len(description) > max_length:
        return description[:max_length] + "..."
    return description

# Получаем название из буфера обмена
title = pyperclip.paste().strip()

# Проверяем, на каком языке название
if is_russian(title):
    print("🔍 Название на русском. Пробуем найти книгу по оригинальному названию...")
    book = search_book(title)

    # Если книга не найдена, пробуем перевести и поискать снова
    if not book:
        print("🔍 Книга не найдена. Пробуем перевести название на английский...")
        translated_title = translate_to_english(title)
        if translated_title:
            print(f"Перевод названия: {translated_title}")
            book = search_book(translated_title)
else:
    print("🔍 Название на английском. Пробуем найти книгу...")
    book = search_book(title)

# Если данные найдены, создаём Markdown-файл
if book:
    volume_info = book.get("volumeInfo", {})
    title = volume_info.get("title", "Без названия")
    authors = volume_info.get("authors", ["Автор неизвестен"])
    published_date = volume_info.get("publishedDate", "Дата неизвестна")
    description = shorten_description(volume_info.get("description", "Описание отсутствует."))
    categories = volume_info.get("categories", [])
    cover_url = volume_info.get("imageLinks", {}).get("thumbnail", "")

    # Форматируем авторов, год и жанры в ссылки
    authors_links = format_as_links(authors)
    year_link = f"[[{published_date}]]" if published_date else "[[Год неизвестен]]"
    genres_links = format_as_links(categories)

    # Добавляем обложку, если она есть
    cover_md = f"![Обложка]({cover_url})" if cover_url else ""

    md_template = f"""---
title: {title}
author: {", ".join(authors)}
year: {published_date}
genre: {", ".join(categories) if categories else "Жанр неизвестен"}
description: {description}
type: book
cover: {cover_url}
---

# {title}

{cover_md}

**Автор:** {authors_links}  
**Год:** {year_link}  
**Жанр:** {genres_links}  

## Описание
{description}

[[Рекомендации]]
[[Библиотека]]
"""


    # Сохраняем файл в папке Obsidian
    file_name = f"{title}.md"
    file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_template)
    
    print(f"✅ Файл {file_name} создан в папке Obsidian!")
else:
    print("❌ Ошибка: Книга не найдена. Проверь название.")

