# Google Antigravity

**Гибридная система коммуникаций и менеджмента задач для университетов.**

## 🚀 Быстрый старт

### 1. Требования
- Python 3.12+
- PostgreSQL 15+ (или Docker)
- Flutter SDK (для мобильного приложения)

### 2. Запуск PostgreSQL (через Docker)
```bash
docker-compose up -d
```

### 3. Запуск Backend
```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Swagger UI
Откройте http://localhost:8000/docs для интерактивной документации API.

## 📁 Структура проекта

```
google_antigravity/
├── docker-compose.yml          # PostgreSQL контейнер
├── backend/
│   ├── .env                    # Конфигурация окружения
│   ├── requirements.txt        # Python-зависимости
│   ├── alembic/                # Миграции БД
│   └── app/
│       ├── main.py             # FastAPI точка входа
│       ├── database.py         # Подключение к БД
│       ├── core/
│       │   ├── config.py       # Настройки приложения
│       │   └── security.py     # JWT + bcrypt
│       ├── models/
│       │   ├── user.py         # Модель пользователя (роли)
│       │   ├── chat.py         # Чаты, сообщения, ветки
│       │   └── task.py         # Задачи (Канбан)
│       ├── schemas/
│       │   ├── user.py         # Pydantic-схемы пользователей
│       │   ├── chat.py         # Pydantic-схемы чатов
│       │   └── task.py         # Pydantic-схемы задач
│       ├── crud/
│       │   ├── crud_user.py    # CRUD пользователей
│       │   ├── crud_chat.py    # CRUD чатов и сообщений
│       │   └── crud_task.py    # CRUD задач
│       └── api/
│           ├── deps.py         # Зависимости (auth guards)
│           └── routes/
│               ├── auth.py     # /auth/register, /auth/login
│               ├── users.py    # /users/me, /users/
│               ├── chats.py    # /chats/, /chats/{id}/messages
│               ├── tasks.py    # /chats/{id}/tasks/
│               └── websocket.py# /ws/{chat_id}
└── frontend/                   # (Flutter — скоро)
```

## 🔑 API Endpoints

| Метод  | Endpoint                               | Описание                        |
|--------|----------------------------------------|---------------------------------|
| POST   | `/api/v1/auth/register`                | Регистрация                     |
| POST   | `/api/v1/auth/login`                   | Вход (JWT)                      |
| GET    | `/api/v1/users/me`                     | Профиль                         |
| POST   | `/api/v1/chats/`                       | Создать чат/группу/канал        |
| GET    | `/api/v1/chats/`                       | Мои чаты                        |
| POST   | `/api/v1/chats/{id}/messages`          | Отправить сообщение             |
| GET    | `/api/v1/chats/{id}/messages`          | Получить сообщения              |
| POST   | `/api/v1/chats/{id}/tasks/`            | Создать задачу                  |
| GET    | `/api/v1/chats/{id}/tasks/`            | Задачи (Канбан)                 |
| POST   | `/api/v1/chats/{id}/tasks/from-message`| Сообщение → Задача              |
| WS     | `/ws/{chat_id}`                        | Real-time сообщения             |

## 🎭 Ролевая модель

| Роль       | Полномочия                                      |
|------------|--------------------------------------------------|
| `student`  | Чтение каналов, личные чаты, задачи              |
| `starosta` | Модерация группы, назначение задач, закрепления   |
| `assistant`| Публикация заданий, мониторинг прогресса          |
| `admin`    | Управление аккаунтами, системные настройки        |
