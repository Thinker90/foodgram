## FOODGRAM

### Описание:



### Использованные технологии:

Python 3.9.10
Django 3.2
Django REST Framework 3.12.4
djangorestframework-simplejwt 5.3.1


### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

```
cd foodgram/backend/
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Зайти в папку с проектом

```
cd backend
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

### Наполнение БД:

Для наполнения БД из csv-файлов используйте команду
```
python3 manage.py import_csv ../data/
```


### API:


```
Для аутентификации используются JWT-токены и библиотека djangorestframework-simplejwt.
auth/ - Регистрация пользователей и выдача токенов. Реализовано разделение по ролям пользователей: Аноним, Аутентифицированный пользователь, Модератор, Администратор.
```

```
users/ - Пользователи
* Для Авторизованного пользователя для своей учетной записи:
    получение данных своей учетной записи, изменение данных своей учетной записи
Для списка всех пользователей реализован поиск по имени пользователя(username).
```

```
recipes/ - Произведения, к которым пишут отзывы
 
```

### Автор, контактная информация:

Алексей Мальцев
* https://github.com/Thinker90
* e-mail: lexa.thinker@gmail.com


