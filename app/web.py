import os

import psycopg
from flask import Flask, Response, current_app, jsonify, request, send_from_directory
from prometheus_client import (
    CollectorRegistry,
    Counter,
    GCCollector,
    PlatformCollector,
    ProcessCollector,
)
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from prometheus_flask_exporter import PrometheusMetrics
from psycopg.rows import dict_row


TASK_FIELDS = "id, title, description, done, created_at, updated_at"


def task_json(row):
    return {
        **row,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def task_input(data):
    if not isinstance(data, dict):
        return None, "Expected a JSON object"

    title = data.get("title")
    description = data.get("description", "")
    done = data.get("done", False)

    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
        return None, "Title must contain 1 to 120 characters"
    if not isinstance(description, str) or len(description) > 1000:
        return None, "Description must contain at most 1000 characters"
    if not isinstance(done, bool):
        return None, "Done must be a boolean"

    return (title.strip(), description, done), None


def create_app(database_url=None):
    app = Flask(__name__, static_folder="static")
    app.config["DATABASE_URL"] = database_url or os.environ["DATABASE_URL"]
    registry = CollectorRegistry(auto_describe=True)
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)
    GCCollector(registry=registry)
    metrics = PrometheusMetrics(app, path=None, group_by="url_rule", registry=registry)
    tasks_created = Counter("taskboard_tasks_created_total", "Tasks created", registry=registry)
    tasks_updated = Counter("taskboard_tasks_updated_total", "Tasks updated", registry=registry)
    tasks_completed = Counter("taskboard_tasks_completed_total", "Tasks marked done", registry=registry)
    tasks_deleted = Counter("taskboard_tasks_deleted_total", "Tasks deleted", registry=registry)

    def connect():
        return psycopg.connect(current_app.config["DATABASE_URL"], row_factory=dict_row)

    @app.get("/metrics")
    @metrics.do_not_track()
    def metrics_endpoint():
        return Response(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    @app.get("/readyz")
    def ready():
        with connect() as connection:
            connection.execute("SELECT 1 FROM tasks LIMIT 0")
        return {"status": "ok"}

    @app.get("/api/tasks")
    def list_tasks():
        with connect() as connection:
            rows = connection.execute(
                f"SELECT {TASK_FIELDS} FROM tasks ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return jsonify([task_json(row) for row in rows])

    @app.post("/api/tasks")
    def create_task():
        values, error = task_input(request.get_json(silent=True))
        if error:
            return {"error": error}, 400

        with connect() as connection:
            row = connection.execute(
                f"INSERT INTO tasks (title, description, done) VALUES (%s, %s, %s) RETURNING {TASK_FIELDS}",
                values,
            ).fetchone()
        tasks_created.inc()
        if row["done"]:
            tasks_completed.inc()
        return jsonify(task_json(row)), 201, {"Location": f"/api/tasks/{row['id']}"}

    @app.get("/api/tasks/<int:task_id>")
    def get_task(task_id):
        with connect() as connection:
            row = connection.execute(
                f"SELECT {TASK_FIELDS} FROM tasks WHERE id = %s", (task_id,)
            ).fetchone()
        if row is None:
            return {"error": "Task not found"}, 404
        return jsonify(task_json(row))

    @app.put("/api/tasks/<int:task_id>")
    def update_task(task_id):
        values, error = task_input(request.get_json(silent=True))
        if error:
            return {"error": error}, 400

        with connect() as connection:
            existing = connection.execute(
                "SELECT done FROM tasks WHERE id = %s FOR UPDATE", (task_id,)
            ).fetchone()
            if existing is None:
                return {"error": "Task not found"}, 404
            row = connection.execute(
                f"""UPDATE tasks
                    SET title = %s, description = %s, done = %s, updated_at = now()
                    WHERE id = %s RETURNING {TASK_FIELDS}""",
                (*values, task_id),
            ).fetchone()
        tasks_updated.inc()
        if not existing["done"] and row["done"]:
            tasks_completed.inc()
        return jsonify(task_json(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        with connect() as connection:
            row = connection.execute(
                "DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,)
            ).fetchone()
        if row is None:
            return {"error": "Task not found"}, 404
        tasks_deleted.inc()
        return "", 204

    return app
