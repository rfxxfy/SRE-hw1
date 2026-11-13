# Grafana в Minikube

Команды выполняются из корня репозитория. Предполагается, что приложение, PostgreSQL и VictoriaMetrics из предыдущих заданий уже запущены.

```sh
docker build -t taskboard:grafana-v1 .
minikube image load taskboard:grafana-v1
kubectl apply -f k8s/05-probe.yaml
kubectl rollout status deployment/taskboard-probe --timeout=180s

helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update grafana-community
python3 grafana/build_dashboards.py
kubectl apply -k grafana
helm upgrade --install grafana grafana-community/grafana --version 14.4.1 \
  -n monitoring -f grafana/values.yaml --wait
kubectl -n monitoring port-forward svc/grafana 3000:80
```

Откройте `http://127.0.0.1:3000`. Grafana доступна для просмотра локально без входа. Для редактирования войдите как `admin`; пароль находится в Kubernetes Secret `grafana` в namespace `monitoring`.

Дашборды загружаются из ConfigMap. `taskboard.json` — экспорт приложения, `postgres-exporter.json` — адаптированный импорт [PostgreSQL Database, ID 9628, revision 8](https://grafana.com/grafana/dashboards/9628-postgresql-database/). Исходный JSON каталога сохранён в `postgres-exporter-upstream.json`. Если изменить JSON, выполните `kubectl apply -k grafana` и дождитесь обновления; при необходимости перезапустите Deployment Grafana.

Проверка:

```sh
kubectl get pods -n monitoring
kubectl get pods -l app=taskboard-probe
kubectl -n monitoring port-forward svc/vm-single-victoria-metrics-single-server 8428:8428
curl -G --data-urlencode 'query=taskboard_probe_success' http://127.0.0.1:8428/api/v1/query
curl -G --data-urlencode 'query=pg_up' http://127.0.0.1:8428/api/v1/query
```
