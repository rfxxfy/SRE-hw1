#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
clear

run() {
    printf '\n$'
    printf ' %s' "$@"
    printf '\n'
    "$@"
    sleep 3
}

run kubectl apply -f k8s/
run kubectl wait --for=condition=complete job/taskboard-migrate --timeout=180s
run kubectl rollout status deployment/taskboard-web --timeout=180s
run kubectl get pods -A
run kubectl scale deployment/taskboard-web --replicas=3
run kubectl rollout status deployment/taskboard-web --timeout=180s
run kubectl get pods -l app=taskboard-web

printf '\n$ kubectl port-forward service/taskboard-web 8080:8000\n'
kubectl port-forward service/taskboard-web 8080:8000
