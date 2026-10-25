# Метрики в Minikube

Нужны работающий Minikube, Docker, kubectl и Helm. Команды выполняются из корня репозитория. VictoriaMetrics Single 0.49.0 собирает метрики сама; отдельный vmagent не установлен.

```sh
docker build -t taskboard:k8s-v2 .
minikube image load taskboard:k8s-v2
docker pull quay.io/prometheuscommunity/postgres-exporter:v0.20.1
minikube image load quay.io/prometheuscommunity/postgres-exporter:v0.20.1
kubectl apply -f k8s/
kubectl wait --for=condition=complete job/taskboard-migrate --timeout=180s
kubectl rollout status deployment/taskboard-postgres --timeout=180s
kubectl rollout status deployment/taskboard-web --timeout=180s
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
helm upgrade --install vm-single vm/victoria-metrics-single --version 0.49.0 -n monitoring --create-namespace -f monitoring/values.yaml --wait
```

Архив также содержит скачанный чарт `monitoring/victoria-metrics-single-0.49.0.tgz`. При необходимости можно передать этот файл Helm вместо имени `vm/victoria-metrics-single` и опустить `--version`.

Если в кластере уже есть Job `taskboard-migrate` из прошлого задания, перед `kubectl apply` удалите только завершённую Job: `kubectl delete job taskboard-migrate`. Kubernetes не разрешает изменить её шаблон Pod.

Проверка:

```sh
kubectl get pods -n monitoring
kubectl get svc -n monitoring
kubectl get pods -l app=taskboard-web
kubectl get pods -l app=taskboard-postgres
kubectl port-forward -n monitoring svc/vm-single-victoria-metrics-single-server 8428:8428
```

В другом терминале:

```sh
curl http://127.0.0.1:8428/api/v1/targets
curl -G --data-urlencode 'query=up' http://127.0.0.1:8428/api/v1/query
curl -G --data-urlencode 'query=taskboard_tasks_created_total' http://127.0.0.1:8428/api/v1/query
curl -G --data-urlencode 'query=pg_up' http://127.0.0.1:8428/api/v1/query
curl http://127.0.0.1:8428/api/v1/label/__name__/values
```

`monitoring/demo.sh` выполняет эти проверки последовательно и выводит значения основных метрик.

В `/targets` должны иметь `health: up` все реплики веб-приложения на `:8000/metrics` и PostgreSQL exporter на `:9187/metrics`. Метрики обновляются каждые 15 секунд. Для проверки через UI откройте приложение командой `kubectl port-forward svc/taskboard-web 8080:8000` и создайте, измените или удалите задачу. Счётчики бизнес-операций принадлежат отдельным Pod; для общей суммы используйте `sum(taskboard_tasks_created_total)`.

Оба Service имеют тип ClusterIP. Путь `/metrics` не требует авторизации и доступен внутри кластера; наружный Ingress для него не создаётся.
