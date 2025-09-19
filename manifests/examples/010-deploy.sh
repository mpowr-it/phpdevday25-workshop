#!/usr/bin/env bash
# --
# @version: 1.0.0
# @purpose: Shell script to run simple secret-generation and pod deployment
# --

#
# create opaque secret from literal (username, password)
# --

kubectl -n default create secret generic sample-00-opaque \
  --from-literal=username=app \
  --from-literal=password=S3cur3-Pa55w0rd123 || true

#
# create the corresponding k8s pod, mount and print-out the corresponding secret
# --
kubectl apply -f 010-deploy.yaml
kubectl logs deployment/secret-pod-test -n default

#
# remove pod and secret
# --
# kubectl delete -f 010-pod.yaml
# kubectl delete secret sample-00-opaque -n default
