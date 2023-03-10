![foodgram-project-react_workflow](https://github.com/Karina-Rin/foodgram-project-react/workflows/foodgram-project-react_workflow.yml/badge.svg)

# Foodgram

## Описание проекта
Приложение «Продуктовый помощник»: сайт, на котором пользователи будут 
публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на 
публикации других авторов. Сервис «Список покупок» позволит пользователям 
создавать список продуктов, которые нужно купить для приготовления выбранных 
блюд. 

На этом сервисе пользователи смогут публиковать рецепты, подписываться на 
публикации других пользователей, добавлять понравившиеся рецепты в список 
«Избранное», а перед походом в магазин скачивать сводный список продуктов, 
необходимых для приготовления одного или нескольких выбранных блюд.

Подписка на публикации доступна только авторизованному пользователю. Страница 
подписок доступна только владельцу.


## Запуск приложения

1. Клонируем репозиторий:
```
git clone https://github.com/Karina-Rin/foodgram-project-react.git
```

2. Создаем `.env` файл с переменными окружения для работы с базой данных в 
директории `infra/` по примеру файла `.env.sample`

3. Запускаем сборку образа в директории backend:
```
docker build -t <DOCKER_USERNAME>/foodgram:<tag> .
```

4. Создаем и активируем виртуальное окружение, обновляем pip:
```
python -m venv venv
. venv/bin/activate
python -m pip install --upgrade pip
```

5. Устанавливаем зависимости:
```
pip install -r requirements.txt
```
6. Подготавливаем репозиторий на GitHub

В репозитории на GitHub прописываем Secrets:
```
DOCKER_USERNAME - имя пользователя DockerHub
DOCKER_PASSWORD - пароль пользователя DockerHub
HOST - IP сервера
USER - текущий пользователь
SSH_KEY - приватный ssh-ключ (начало -----BEGIN OPENSSH PRIVATE KEY----- ... -----END OPENSSH PRIVATE KEY----- конец)
PASSPHRASE - кодовая фраза для ssh-ключа (если ваш ssh-ключ защищён фразой-паролем)
TELEGRAM_TO - ID своего телеграм-аккаунта. Узнать можно у бота `@userinfobot`
TELEGRAM_TOKEN - токен вашего бота. Получить можно у бота `@BotFather`
```

7. Запускаем сборку контейнеров:
```
docker-compose up -d --build
```

8. Переходим в контейнер
```
sudo docker container exec -it <CONTAINER ID> bash
```
Выполняем миграции
```
sudo python manage.py makemigrations users
sudo python manage.py makemigrations recipes
```
Применяем миграции
```
sudo python manage.py migrate
```
Создаем суперюзера
```
sudo python manage.py createsuperuser
```
Собираем статистику
```
sudo python manage.py collectstatic --no-input
```
Наполняем данными
```
sudo python manage.py importcsv --filename ingredients.csv --model_name Ingredient --app_name recipes
sudo python manage.py importcsv --filename tags.csv --model_name Tag --app_name recipes
```

### Запуск проекта
#### Тестовые данные для проверки ревьюером:

```bash
# Админ
http://62.84.120.208/admin
Login: 
Password: 

# Тестовый пользователь
http://62.84.120.208/
Email: 
Password: 
```

#### Адрес проекта
http://62.84.120.208/

#### Документация
http://62.84.120.208/api/docs/

## Авторы
Karina-Rin