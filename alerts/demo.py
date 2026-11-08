import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def request(method, path, data):
    body = json.dumps(data).encode()
    req = Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(req, timeout=10) as response:
        return json.load(response) if response.status != 204 else None


time.sleep(20)
ids = []
try:
    for number in range(5):
        task = request("POST", "/api/tasks", {"title": f"Проверка алертов {number}"})
        ids.append(task["id"])
        request(
            "PUT",
            f"/api/tasks/{task['id']}",
            {"title": f"Проверка алертов {number} обновлена"},
        )
    for _ in range(8):
        try:
            request("POST", "/api/tasks", {"title": ""})
        except HTTPError as error:
            if error.code != 400:
                raise
finally:
    for task_id in ids:
        request("DELETE", f"/api/tasks/{task_id}", {})

print("Создано, изменено и удалено 5 тестовых задач; выполнено 8 запросов с ответом 400.")
