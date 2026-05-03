"""Полный интеграционный тест API Google Antigravity."""
import requests
import json
import sys

BASE = "http://127.0.0.1:8000/api/v1"

# 1) Регистрация
print("=== РЕГИСТРАЦИЯ ===")
r = requests.post(f"{BASE}/auth/register", json={
    "email": "test2@student.university.kz",
    "password": "secret123",
    "full_name": "Тест Студент 2"
})
if r.status_code == 400:
    print("Пользователь уже существует, пропускаем")
else:
    print(f"Status: {r.status_code}")
    print(f"Body: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")

# 2) Вход
print("\n=== ВХОД ===")
r = requests.post(f"{BASE}/auth/login", json={
    "email": "test2@student.university.kz",
    "password": "secret123"
})
print(f"Status: {r.status_code}")
token_data = r.json()
token = token_data["access_token"]
print(f"Token: {token[:40]}...")

# 3) Профиль
print("\n=== ПРОФИЛЬ ===")
headers = {"Authorization": f"Bearer {token}"}
r = requests.get(f"{BASE}/users/me", headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")

# 4) Создание чата
print("\n=== СОЗДАНИЕ ЧАТА ===")
r = requests.post(f"{BASE}/chats/", headers=headers, json={
    "name": "Алгоритмы и СД - CS-101",
    "description": "Чат для обсуждения предмета",
    "chat_type": "group"
})
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
chat = r.json()
print(f"Body: {json.dumps(chat, indent=2, ensure_ascii=False)}")
chat_id = chat["id"]

# 5) Отправка сообщения с Markdown
print("\n=== ОТПРАВКА СООБЩЕНИЯ (Markdown) ===")
r = requests.post(f"{BASE}/chats/{chat_id}/messages", headers=headers, json={
    "content": "# Домашнее задание\n\nРеализовать **Bubble Sort** на Python.\nДедлайн: **5 мая**"
})
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
msg = r.json()
print(f"Message ID: {msg['id']}")

# 5.1) Отправка сообщения с файлом
print("\n=== ОТПРАВКА СООБЩЕНИЯ С ФАЙЛОМ ===")
with open("test_file.txt", "w") as f:
    f.write("This is a test file for upload.")

with open("test_file.txt", "rb") as f:
    files = {"file": ("test_file.txt", f, "text/plain")}
    data = {"content": "Attached a test file!"}
    r = requests.post(f"{BASE}/chats/{chat_id}/messages/upload", headers=headers, files=files, data=data)

print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
msg_with_file = r.json()
print(f"Message ID: {msg_with_file['id']}, File URL: {msg_with_file['file_url']}")

# 6) Конвертация сообщение -> задача
print("\n=== КОНВЕРТАЦИЯ СООБЩЕНИЕ -> ЗАДАЧА ===")
r = requests.post(
    f"{BASE}/chats/{chat_id}/tasks/from-message",
    headers=headers,
    params={"message_id": msg["id"], "title": "ДЗ: Реализовать Bubble Sort"}
)
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
print(f"Body: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")

# 7) Создание ещё одной задачи
print("\n=== СОЗДАНИЕ ЗАДАЧИ ===")
r = requests.post(f"{BASE}/chats/{chat_id}/tasks/", headers=headers, json={
    "title": "Подготовить презентацию по алгоритмам",
    "priority": "high",
    "description": "Слайды по теме сортировок"
})
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)

# 8) Канбан-доска
print("\n=== КАНБАН-ДОСКА ===")
r = requests.get(f"{BASE}/chats/{chat_id}/tasks/", headers=headers)
print(f"Status: {r.status_code}")
tasks = r.json()
print(f"Задач на доске: {len(tasks)}")
for task in tasks:
    print(f"  [{task['status']}] {task['title']} (приоритет: {task['priority']})")

# 9) Поиск сообщений
print("\n=== ПОИСК СООБЩЕНИЙ ===")
r = requests.get(f"{BASE}/chats/{chat_id}/search/messages", headers=headers, params={"query": "Bubble Sort"})
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
searched_msgs = r.json()
print(f"Найдено сообщений: {len(searched_msgs)}")
for sm in searched_msgs:
    print(f"  ID: {sm['id']}, Content: {sm['content'][:30]}...")

# 10) Поиск задач
print("\n=== ПОИСК ЗАДАЧ ===")
r = requests.get(f"{BASE}/chats/{chat_id}/search/tasks", headers=headers, params={"query": "презентацию"})
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(f"Error: {r.text}")
    sys.exit(1)
searched_tasks = r.json()
print(f"Найдено задач: {len(searched_tasks)}")
for st in searched_tasks:
    print(f"  ID: {st['id']}, Title: {st['title']}")

print("\n" + "=" * 50)
print("  ALL TESTS PASSED SUCCESSFULLY!")
print("=" * 50)
