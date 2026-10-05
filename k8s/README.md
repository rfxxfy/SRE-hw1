# Запуск в Minikube

Нужны Docker, Minikube и kubectl. На macOS с Colima сначала запустите Docker: `colima start --cpu 4 --memory 4`.

```sh
minikube start --driver=docker --container-runtime=docker --cpus=2 --memory=3072
eval "$(minikube docker-env)"
docker build -t taskboard:k8s-v1 .
docker save taskboard:k8s-v1 -o /tmp/taskboard-k8s-v1.tar
eval "$(minikube docker-env -u)"
minikube image load /tmp/taskboard-k8s-v1.tar
docker pull postgres:16-alpine
minikube image load postgres:16-alpine
rm /tmp/taskboard-k8s-v1.tar
kubectl run kubectl-practice --image=taskboard:k8s-v1 --image-pull-policy=Never --restart=Never --command -- python -c 'print("kubectl-ok")'
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/kubectl-practice --timeout=90s
kubectl get pod kubectl-practice
kubectl logs kubectl-practice
kubectl describe pod kubectl-practice
kubectl delete pod kubectl-practice
kubectl apply -f k8s/
kubectl wait --for=condition=complete job/taskboard-migrate --timeout=180s
kubectl rollout status deployment/taskboard-web --timeout=180s
kubectl get pods -A
```

Откройте доступ к приложению в отдельном терминале:

```sh
kubectl port-forward service/taskboard-web 8080:8000
```

Интерфейс будет доступен по адресу <http://localhost:8080>. Масштабирование веб-приложения:

```sh
kubectl scale deployment/taskboard-web --replicas=3
kubectl rollout status deployment/taskboard-web
kubectl get pods -l app=taskboard-web
```

PostgreSQL оставляется в одной реплике, поскольку он использует один постоянный том. Пароль в `00-secret.yaml` — учебное значение для локального Minikube. Для другого окружения замените его перед запуском.

Удалить ресурсы задания: `kubectl delete -f k8s/`. Удаление PVC удалит данные БД.
