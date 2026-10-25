#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
clear

run() {
    printf '\n$'
    printf ' %s' "$@"
    printf '\n'
    "$@"
    sleep 2
}

query() {
    printf '\n$ curl -G --data-urlencode "query=%s" http://127.0.0.1:8428/api/v1/query\n' "$1"
    curl -fsS -G --data-urlencode "query=$1" http://127.0.0.1:8428/api/v1/query |
        python3 -c 'import json,sys; result=json.load(sys.stdin)["data"]["result"]; print("\n".join("%s pod=%s value=%s" % (item["metric"].get("app"), item["metric"].get("pod"), item["value"][1]) for item in result))'
    sleep 2
}

run kubectl get pods -n monitoring
run kubectl get svc -n monitoring
run kubectl get pods -l app=taskboard-web
run kubectl get pods -l app=taskboard-postgres

printf '\n$ kubectl port-forward -n monitoring svc/vm-single-victoria-metrics-single-server 8428:8428\n'
log_file=$(mktemp)
kubectl port-forward -n monitoring svc/vm-single-victoria-metrics-single-server 8428:8428 >"$log_file" 2>&1 &
forward_pid=$!
trap 'kill "$forward_pid" 2>/dev/null || true; rm -f "$log_file"' EXIT INT TERM
until curl -fsS --max-time 1 http://127.0.0.1:8428/health >/dev/null 2>&1; do
    if ! kill -0 "$forward_pid" 2>/dev/null; then
        cat "$log_file"
        exit 1
    fi
    sleep 1
done
cat "$log_file"
sleep 2

printf '\n$ curl http://127.0.0.1:8428/api/v1/targets\n'
curl -fsS http://127.0.0.1:8428/api/v1/targets |
    python3 -c 'import json,sys; targets=json.load(sys.stdin)["data"]["activeTargets"]; print("\n".join("%s %s %s" % (item["health"], item["labels"].get("app"), item["scrapeUrl"]) for item in targets))'
sleep 2

query up
query process_resident_memory_bytes
query flask_http_request_total
query taskboard_tasks_created_total
query taskboard_tasks_updated_total
query taskboard_tasks_completed_total
query taskboard_tasks_deleted_total
query pg_up

printf '\nПроверка завершена.\n'
