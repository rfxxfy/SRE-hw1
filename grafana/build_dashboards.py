import json
import re
from pathlib import Path


ROOT = Path(__file__).parent
DATASOURCE = {"type": "prometheus", "uid": "victoriametrics"}


def panel(panel_id, title, expression, x, y, width=6, height=6, kind="timeseries", unit="short", description=""):
    return {
        "id": panel_id,
        "title": title,
        "type": kind,
        "description": description,
        "datasource": DATASOURCE,
        "gridPos": {"x": x, "y": y, "w": width, "h": 4 if kind == "stat" else height},
        "targets": [{"datasource": DATASOURCE, "expr": expression, "refId": "A", "legendFormat": "{{pod}}" if kind == "timeseries" else "", "instant": kind == "stat"}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "orientation": "auto", "textMode": "auto"} if kind == "stat" else {"legend": {"displayMode": "list", "placement": "bottom"}},
    }


def main():
    panels = [
        panel(1, "Веб: доступные реплики", 'sum(up{app="taskboard-web"})', 0, 0, kind="stat", description="Число реплик, с которых VictoriaMetrics успешно собрала метрики."),
        panel(2, "PostgreSQL: подключение", 'max(pg_up{app="taskboard-postgres"})', 6, 0, kind="stat", description="postgres_exporter смог подключиться к базе: 1 — да, 0 — нет."),
        panel(3, "Пробер: последняя проверка", 'taskboard_probe_success{app="taskboard-probe"}', 12, 0, kind="stat", description="Проверка /readyz и GET /api/tasks: 1 — успех, 0 — ошибка."),
        panel(4, "SLA: успешные проверки за 24 ч", '100 * sum(increase(taskboard_probe_checks_total{app="taskboard-probe",result="success"}[24h])) / clamp_min(sum(increase(taskboard_probe_checks_total{app="taskboard-probe"}[24h])), 1)', 18, 0, kind="stat", unit="percent", description="Доля успешных проверок за последние 24 часа. Целевой SLO — 99,9%."),
        panel(5, "RPS API", 'sum(rate(flask_http_request_duration_seconds_count{app="taskboard-web",url_rule=~"/api/tasks.*"}[$__rate_interval]))', 0, 4, width=8, unit="reqps", description="Нагрузка на API задач без служебных health-запросов."),
        panel(6, "Ошибки API, %", '100 * (sum(rate(flask_http_request_duration_seconds_count{app="taskboard-web",url_rule=~"/api/tasks.*",status=~"5.."}[$__rate_interval])) or vector(0)) / clamp_min(sum(rate(flask_http_request_duration_seconds_count{app="taskboard-web",url_rule=~"/api/tasks.*"}[$__rate_interval])), 0.001)', 8, 4, width=8, unit="percent", description="Доля ответов 5xx среди запросов к API."),
        panel(7, "Задержка API p95", 'histogram_quantile(0.95, sum by (le) (rate(flask_http_request_duration_seconds_bucket{app="taskboard-web",url_rule=~"/api/tasks.*"}[$__rate_interval])))', 16, 4, width=8, unit="s", description="95-й процентиль времени ответа API."),
        panel(8, "Создание задач за 1 ч", 'sum(increase(taskboard_tasks_created_total{app="taskboard-web"}[1h]))', 0, 10, kind="stat", description="Успешно созданные задачи за последний час."),
        panel(9, "Изменение задач за 1 ч", 'sum(increase(taskboard_tasks_updated_total{app="taskboard-web"}[1h]))', 6, 10, kind="stat", description="Успешно изменённые задачи за последний час."),
        panel(10, "Завершение задач за 1 ч", 'sum(increase(taskboard_tasks_completed_total{app="taskboard-web"}[1h]))', 12, 10, kind="stat", description="Задачи, переведённые в выполненные за последний час."),
        panel(11, "Удаление задач за 1 ч", 'sum(increase(taskboard_tasks_deleted_total{app="taskboard-web"}[1h]))', 18, 10, kind="stat", description="Успешно удалённые задачи за последний час."),
        panel(12, "Память Python-процесса", 'process_resident_memory_bytes{app="taskboard-web"}', 0, 14, width=8, unit="bytes", description="RSS каждого Pod. Лимит контейнера — 256 MiB."),
        panel(13, "CPU Python-процесса", 'rate(process_cpu_seconds_total{app="taskboard-web"}[$__rate_interval])', 8, 14, width=8, unit="percentunit", description="Доля одного CPU, потребляемая процессом."),
        panel(14, "Сборки мусора Python / с", 'sum by (generation) (rate(python_gc_collections_total{app="taskboard-web"}[$__rate_interval]))', 16, 14, width=8, unit="ops", description="Частота сборок мусора по поколениям."),
        panel(15, "Проверки пробера", 'sum by (result) (rate(taskboard_probe_checks_total{app="taskboard-probe"}[$__rate_interval]))', 0, 20, width=12, unit="ops", description="Успешные и неуспешные проверки в секунду."),
        panel(16, "Время проверки пробера p95", 'histogram_quantile(0.95, sum by (le) (rate(taskboard_probe_duration_seconds_bucket{app="taskboard-probe"}[$__rate_interval])))', 12, 20, width=12, unit="s", description="Время проверки готовности и API."),
    ]
    for item in panels:
        if item["id"] in (1, 2, 3):
            item["fieldConfig"]["defaults"]["thresholds"] = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]}
            item["fieldConfig"]["defaults"]["color"] = {"mode": "thresholds"}
        if item["id"] == 4:
            item["fieldConfig"]["defaults"]["thresholds"] = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 99.9}]}
            item["fieldConfig"]["defaults"]["color"] = {"mode": "thresholds"}
    dashboard = {
        "uid": "taskboard-overview",
        "title": "Taskboard — сервис и SLA",
        "tags": ["taskboard", "sre", "sla"],
        "timezone": "browser",
        "schemaVersion": 41,
        "version": 1,
        "refresh": "15s",
        "time": {"from": "now-15m", "to": "now"},
        "panels": panels,
        "annotations": {"list": []},
    }
    (ROOT / "taskboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n")

    postgres = json.loads((ROOT / "postgres-exporter-upstream.json").read_text())
    postgres["uid"] = "taskboard-postgres"
    postgres["title"] = "PostgreSQL Exporter — Taskboard"
    postgres["id"] = None
    postgres["version"] = 1
    postgres["refresh"] = "15s"
    postgres["time"] = {"from": "now-1h", "to": "now"}
    postgres["templating"]["list"] = [
        {"name": "instance", "label": "Exporter", "type": "query", "datasource": DATASOURCE, "query": "label_values(pg_up{app=\"taskboard-postgres\"}, instance)", "refresh": 1, "current": {}},
        {"name": "datname", "label": "Database", "type": "query", "datasource": DATASOURCE, "query": "label_values(pg_stat_database_numbackends{app=\"taskboard-postgres\"}, datname)", "refresh": 1, "includeAll": True, "allValue": ".*", "current": {"text": "All", "value": "$__all"}},
        {"name": "mode", "label": "Lock mode", "type": "query", "datasource": DATASOURCE, "query": "label_values(pg_locks_count{app=\"taskboard-postgres\"}, mode)", "refresh": 1, "includeAll": True, "allValue": ".*", "current": {"text": "All", "value": "$__all"}},
    ]

    def adapt(value):
        if isinstance(value, dict):
            value.pop("__inputs", None)
            for key, item in list(value.items()):
                if key == "expr" and isinstance(item, str):
                    item = re.sub(r',?\s*release="\$release"', "", item)
                    item = re.sub(r'\{\s*,', "{", item)
                    value[key] = item
                elif key == "datasource":
                    value[key] = DATASOURCE
                else:
                    adapt(item)
        elif isinstance(value, list):
            for item in value:
                adapt(item)

    adapt(postgres)
    for item in postgres["panels"]:
        if item.get("id") == 28:
            item["title"] = "Exporter up"
            item["format"] = "short"
            item["targets"][0]["expr"] = 'pg_up{app="taskboard-postgres",instance="$instance"}'
        elif item.get("id") == 10:
            item["format"] = "short"
        elif item.get("id") == 24:
            for target in item["targets"]:
                target["expr"] = target["expr"].replace("avg(rate(", "avg(").replace("[5m]))", ")")
    (ROOT / "postgres-exporter.json").write_text(json.dumps(postgres, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
