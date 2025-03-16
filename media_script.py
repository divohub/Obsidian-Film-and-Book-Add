import sys
from dotenv import load_dotenv
import io
import requests
import pyperclip
import argparse
import os
import re
from deep_translator import GoogleTranslator
from transliterate import translit
from logger import setup_logger


load_dotenv()


# Конфигурация
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH_MOVIE")  # Укажи путь к своей папке Obsidian .env
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Вставь свой API-ключ для TMDb в .env


# Настройка логгирования
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging = setup_logger(log_file="script.log")

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
def search_tmdb(title, year=None, content_type="movie"):
    """
    Поиск фильма или сериала на TMDb.

    :param title: Название фильма или сериала.
    :param year: Год выпуска (опционально).
    :param content_type: Тип контента ("movie" для фильмов, "tv" для сериалов).
    :return: Информация о фильме или сериале, либо None, если ничего не найдено.
    """

    if content_type not in ["movie", "tv"]:
        raise ValueError("content_type должен быть movie или tv")
    
    url = f"https://api.themoviedb.org/3/search/{content_type}?api_key={TMDB_API_KEY}&query={title}&language=ru-RU"
    if year:
        url += f"&year={year}"
    
    # Выполняем запрос 
    response = requests.get(url)
    data = response.json()
    
    
    if data.get("results"):
        if year:
            for item in data["results"]:
                release_date = item.get("release_date", "") if content_type == "movie" else item.get("first_air_date", "")
                if release_date.startswith(str(year)):
                    return item
                
        return data["results"][0]  # Возвращаем первый результат
    return None

# Функция для получения деталей фильма по ID
def get_details(id, content_type):
    url = f"https://api.themoviedb.org/3/{content_type}/{id}?api_key={TMDB_API_KEY}&language=ru-RU"
    response = requests.get(url)
    return response.json()

# Функция для получения команды фильма (режиссёры, актёры и т.д.)
def get_credits(id, content_type):
    url = f"https://api.themoviedb.org/3/{content_type}/{id}/credits?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

# Функция для проверки языка текста
def is_russian(text):
    # Проверяем, есть ли в тексте кириллица
    return any('\u0400' <= char <= '\u04FF' for char in text)


def get_input_text(key):
    input_texts = {
        "content_type": ("Введите тип контента (movie/tv)", "Тип контента должен быть movie или tv"),
        "movie_title": ("Введите название фильма", "Название фильма не может быть пустым"),
        "tv_title": ("Введите название сериала", "Название сериала не может быть пустым"),
        "year": ("Ввидете год выпуска", "Год выпуска должен быть числом"),
    }
    if key in input_texts:
        return input_texts[key][0], input_texts[key][1], True
    else:
        return None,"Неизвестный ключ", False
    

def get_input(key):
    user_input_text, error, exists = get_input_text(key)
    if not exists:
        raise ValueError(f"Неизвестный ключ: {key}") 
    while True:
        try:
            user_input = input(f"{user_input_text}: ").strip()
            if key == "content_type" and user_input not in ["movie", "tv"]: raise ValueError
            if key!="year" and not user_input: raise ValueError
            break
        except ValueError:
            logging.error(error)
        except KeyboardInterrupt:
            logging.info("Выход из программы")
            sys.exit(1)
    return user_input

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



def main():
    # Парсинг аргументов
    parser = argparse.ArgumentParser(description="Поиск фильмов и сериалов на TMDb.")
    parser.add_argument("-m", "--movie", action="store_true", help="Искать фильмы")
    parser.add_argument("-t", "--tv", action="store_true", help="Искать сериалы")
    parser.add_argument("-c", "--clipboard", action="store_true", help="Использовать текст из буфера обмена")
    parser.add_argument("--title", help="Название фильма или сериала")
    parser.add_argument("--year", type=int, help="Год выпуска")
    args = parser.parse_args()

    # Выбор типа контента
    if args.movie:
        content_type = "movie"
    elif args.tv:
        content_type = "tv"
    else:
        content_type = get_input("content_type")
 


    if args.clipboard:
        # Получаем текст из буфера обмена
        clipboard_text = pyperclip.paste().strip()

        # Извлекаем год из буфера обмена
        year = extract_year(clipboard_text)

        title = re.sub(r"\b(19\d{2}|20\d{2})\b", "", clipboard_text).strip()

    if not args.clipboard:
        title = get_input(f"{content_type}_title")
            
        
    if not args.clipboard:
        year = get_input("year")

    else :
        ValueError("year должен быть int")    
  




    # Проверяем, на каком языке название
    if is_russian(title):
        logging.info("🔍 Название на русском. Пробуем найти фильм по оригинальному названию...")
        data = search_tmdb(title, year, content_type)

        # Если фильм не найден, пробуем транслитерировать и поискать снова
        if not data:
            logging.info("🔍 Фильм не найден. Пробуем транслитерировать название...")
            transliterated_title = translit(title, 'ru', reversed=True)  # Транслитерация
            logging.info(f"Транслитерированное название: {transliterated_title}") 
            data = search_tmdb(transliterated_title, year, content_type)

            # Если фильм не найден, пробуем перевести и поискать снова
            if not data:
                logging.info("🔍 Фильм не найден. Пробуем перевести название на английский...")
                translated_title = translate_to_english(title)
                if translated_title:
                    print(f"Перевод названия: {translated_title}")
                    data = search_tmdb(translated_title, year, content_type)
    else:
        logging.info("🔍 Название на английском. Пробуем найти фильм...")
        data = search_tmdb(title, year, content_type)

    # Если данные найдены, создаём Markdown-файл
    if data:
        # Получаем детали фильма по ID
        details = get_details(data['id'], content_type)
        
        # Получаем команду фильма (режиссёры, актёры и т.д.)
        credits = get_credits(data['id'], content_type)
        

        # Извлекаем режиссёров (для фильмов) или создателей (для сериалов)
        if content_type == "movie":
            directors = [crew['name'] for crew in credits.get('crew', []) if crew['job'] == 'Director']
        else:
            directors = [creator['name'] for creator in credits.get('created_by', [])]
        
        # Извлекаем пять главных актёров
        top_actors = [actor['name'] for actor in credits.get('cast', [])[:5]]
        
        # Извлекаем данные
        title = details.get("title" if content_type == "movie" else "name", "Без названия")
        year = details.get("release_date" if content_type == "movie" else "first_air_date", "Год неизвестен")[:4]
        description = details.get("overview", "Описание отсутствует.")
        genres = details.get("genres", [])
        poster_path = details.get("poster_path", "")
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
type: {content_type}
cover: {poster_url}
watched: false
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
        
        logging.info(f"✅ File {file_name} создан в папке Obsidian!")
    else:
        logging.error("❌ Ошибка: Фильм не найден. Проверь название.")

if __name__ == "__main__":
    main()