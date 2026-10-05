# Список задач

Небольшое клиент-серверное приложение для хранения задач. Интерфейс написан на обычном HTML, CSS и JavaScript. Сервер предоставляет REST API на Flask, данные хранятся в PostgreSQL.

## Запуск

Нужны Docker и Docker Compose. На этой машине доступна команда `docker-compose`; если у вас установлен плагин Compose, замените её на `docker compose`.

```sh
cp .env.example .env
# При необходимости измените POSTGRES_PASSWORD в .env
docker-compose up --build -d
```

Откройте <http://localhost:8000>. Для другого порта задайте `PORT` в `.env`. Остановить приложение: `docker-compose down`. Данные остаются в томе `postgres_data`; удалить их можно командой `docker-compose down -v`.

Сервис `migrate` создаёт таблицу перед запуском веб-сервера. При повторном запуске команда безопасна. Проверки: `GET /healthz` для процесса и `GET /readyz` для подключения к БД.

## REST API

| Метод и путь | Действие |
| --- | --- |
| `GET /api/tasks` | Список задач |
| `POST /api/tasks` | Создать задачу |
| `GET /api/tasks/{id}` | Получить задачу |
| `PUT /api/tasks/{id}` | Изменить задачу |
| `DELETE /api/tasks/{id}` | Удалить задачу |

Тело для `POST` и `PUT` — JSON: `{"title":"Купить молоко","description":"2 литра","done":false}`. `title` обязателен, остальные поля имеют значения по умолчанию. При ошибке валидации сервер возвращает `400`, для неизвестной задачи — `404`.

## Локальный запуск без Compose

Установите PostgreSQL, создайте базу и задайте `DATABASE_URL` (например, `postgresql://user:password@localhost:5432/tasks`). Затем:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m app.migrate
gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile - app.wsgi:application
```

Структура: `app/web.py` — HTTP API, `app/migrate.py` — создание схемы, `app/static/` — интерфейс, `compose.yaml` — запуск приложения и PostgreSQL.

Для запуска в Kubernetes см. [инструкцию Minikube](k8s/README.md).
