#!/usr/bin/env bash
# --
# @version: 1.0.0
# @purpose: Shell script to create different secret-types
# --

#
# create Sample-Secret-01 Direct (literal) approach
# --
kubectl -n default create secret generic sample-01-opaque \
  --from-literal=username=app \
  --from-literal=password=S3cur3-Pa55w0rd123

#
# create Sample-Secret-02 Indirect (fromFile) appro
# - create simple files with credentials
# - create the Secret from files
# --
echo -n "app" > username.txt
echo -n "S3cur3-Pa55w0rd123" > password.txt

kubectl -n default create secret generic sample-02-opaque \
  --from-file=username=./username.txt \
  --from-file=password=./password.txt

#
# inspect those secrets
# --
kubectl -n default get secret sample-01-opaque -o yaml; \
echo "*********************"; \
kubectl -n default get secret sample-02-opaque -o yaml;

#
# remove all secrets
# --
# kubectl -n default delete secret sample-01-opaque
# kubectl -n default delete secret sample-02-opaque
