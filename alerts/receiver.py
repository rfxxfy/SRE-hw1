import html
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


events = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/alerts":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 1_000_000:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(size))
        except (ValueError, json.JSONDecodeError):
            self.send_error(400)
            return
        for alert in payload.get("alerts", []):
            item = {
                "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": alert.get("status", "unknown"),
                "name": alert.get("labels", {}).get("alertname", "unknown"),
                "severity": alert.get("labels", {}).get("severity", "unknown"),
                "summary": alert.get("annotations", {}).get("summary", ""),
            }
            events.append(item)
            print(json.dumps(item, ensure_ascii=False), flush=True)
        del events[:-100]
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            return
        if self.path == "/events":
            body = json.dumps(events, ensure_ascii=False).encode()
            content_type = "application/json; charset=utf-8"
        elif self.path == "/":
            rows = "".join(
                "<tr><td>{received_at}</td><td>{status}</td><td>{name}</td>"
                "<td>{severity}</td><td>{summary}</td></tr>".format(
                    **{key: html.escape(str(value)) for key, value in event.items()}
                )
                for event in reversed(events)
            )
            body = (
                "<!doctype html><html lang='ru'><meta charset='utf-8'>"
                "<meta http-equiv='refresh' content='5'>"
                "<title>Уведомления Alertmanager</title>"
                "<style>body{font:16px system-ui;margin:40px;background:#f8fafc;color:#172033}"
                "h1{font-size:28px}table{border-collapse:collapse;width:100%;background:white}"
                "th,td{padding:12px;text-align:left;border-bottom:1px solid #dbe2ea}"
                "th{background:#e9eff6}</style>"
                "<h1>Уведомления Alertmanager</h1>"
                "<p>Получены через webhook из кластера Kubernetes.</p>"
                "<table><tr><th>Получено (UTC)</th><th>Статус</th><th>Алерт</th>"
                "<th>Важность</th><th>Описание</th></tr>"
                f"{rows}</table></html>"
            ).encode()
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
