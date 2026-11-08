# Алерты приложения

Нужны работающие Minikube, приложение и VictoriaMetrics Single из предыдущих заданий; порядок их установки описан в `monitoring/README.md`. Образ приложения `taskboard:k8s-v2` должен быть загружен в Minikube. Правила проверяет `vmalert`, уведомления группирует Alertmanager. Учебный webhook-приёмник показывает доставленные уведомления в браузере и пишет их в stdout. Внешний аккаунт для демонстрации не требуется.

## Запуск

```sh
docker pull victoriametrics/vmalert:v1.154.0
docker pull quay.io/prometheus/alertmanager:v0.28.1
minikube image load victoriametrics/vmalert:v1.154.0
minikube image load quay.io/prometheus/alertmanager:v0.28.1
kubectl apply -k alerts/
kubectl rollout status -n monitoring deployment/taskboard-vmalert
kubectl rollout status -n monitoring deployment/taskboard-alertmanager
kubectl rollout status -n monitoring deployment/taskboard-alert-receiver
kubectl get pods -n monitoring
```

`kubectl apply -k` собирает ConfigMap из отдельных файлов `rules.yml`, `alertmanager.yml` и `receiver.py`. При изменении этих файлов имя ConfigMap меняется, а Deployment получает новый шаблон Pod.

## Проверка срабатывания

Скрипт создаёт, изменяет и удаляет пять временных задач, затем отправляет восемь некорректных запросов. Созданные задачи он удаляет. Подождите около минуты после запуска: VictoriaMetrics собирает метрики каждые 15 секунд, а правило должно оставаться истинным 30 секунд.

```sh
kubectl exec -i deployment/taskboard-web -- python - < alerts/demo.py
kubectl logs -n monitoring deployment/taskboard-alert-receiver
```

Откройте три терминала с туннелями:

```sh
kubectl port-forward -n monitoring svc/taskboard-vmalert 18880:8880
kubectl port-forward -n monitoring svc/taskboard-alertmanager 19093:9093
kubectl port-forward -n monitoring svc/taskboard-alert-receiver 18080:8080
```

Страницы: [правила vmalert](http://127.0.0.1:18880/vmalert/groups), [активные алерты Alertmanager](http://127.0.0.1:19093/#/alerts), [доставленные уведомления](http://127.0.0.1:18080/). API: `/api/v1/rules` у vmalert, `/api/v2/alerts` у Alertmanager и `/events` у webhook-приёмника.

Скриншоты проверенной установки находятся в `screenshots/`. Для повторной демонстрации после 10 минут запустите `demo.py` ещё раз. Пороговые значения подобраны для небольшого учебного приложения; в рабочей системе их следует уточнять по обычной нагрузке.

## Файлы

- `rules.yml` — два бизнес-алерта и два алерта на метрики Flask/Python.
- `alertmanager.yml` — маршрут и webhook-получатель.
- `k8s.yaml`, `kustomization.yaml` — развёртывание компонентов.
- `receiver.py` — локальный получатель уведомлений для демонстрации.
- `demo.py` — воспроизводимое срабатывание трёх правил.
- `Отчёт.md` — выбор условий и результаты проверки.
