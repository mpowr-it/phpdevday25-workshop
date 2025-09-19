# Installation Walkthrough Part 4 - OpenResty Lua App

This walkthrough demonstrates how to build, deploy, and validate the sample OpenResty (Nginx + Lua) application
that connects to a PostgreSQL database using secrets managed by the External Secrets Operator (ESO).
It also includes password rotation checks and the use of the Stakater Reloader to reload pods automatically
when secrets or configmaps change.

## Prerequisites

- A running Kubernetes cluster (minimum version **1.32.x**)
- Operators from **Part 1** and **Part 2** must already be installed:
    - CloudNativePG (CNPG)
    - External Secrets Operator (ESO)
    - Stakater Reloader
- A PostgreSQL cluster and synced secret (e.g., `delta-pg` with `delta-pg-app` Secret in namespace `int-app-delta`).

## Build & Push Application Image

The application source code is located in `src/`. Use Docker to build and push the container image.

```bash
# 000.0 - Build & push docker image
docker build -t mpowr/k8s-app-nginx-lua-db:1.0.8 -t mpowr-local/k8s-app-nginx-lua-db:1.0.8 src/
docker push mpowr/k8s-app-nginx-lua-db:1.0.8
```

## Deploy Application

Apply the application deployment manifest (`200-deploy-app.yaml`) to your namespace.
It contains the **Stakater Reloader annotation** to auto-reload the pod when the linked Secret changes.

```bash
# 001.0 - Deploy the Lua app
kubectl -n int-app-delta apply -f 200-deploy-app.yaml

# 001.1 - Check deployment rollout
kubectl -n int-app-delta rollout status deploy/web-app-lua-db-deployment
```

## Check & Evaluate

Validate that secrets are synced correctly and that the app can connect to PostgreSQL.

```bash
# 002.0 - Inspect external secrets + secretstore
kubectl -n int-app-delta get externalsecret,secretstore

# 002.1 - Decode the generated Kubernetes secret
kubectl -n int-app-delta get secret delta-pg-app   -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'

# 002.2 - Export DB connection string
unset DB_URI; export DB_URI="$(kubectl -n int-app-delta get secret delta-pg-app   -o jsonpath='{.data.uri}' | base64 -d)"; echo "$DB_URI"

# 002.3 - Positive Test: Connect with valid credentials inside CNPG pod
kubectl -n int-app-delta exec -it delta-pg-1 --   psql "$DB_URI" -At -c 'select current_user,current_database();'
# >>> Expected: app|app

# 002.4 - Negative Test: Try invalid password
BAD_URI="$(printf '%s' "$DB_URI" | sed -E 's#(postgresql://[^:]+:)[^@]+#\1WRONG#')"; echo "$BAD_URI"
kubectl -n int-app-delta exec -it delta-pg-1 --   psql "$BAD_URI" -c 'select 1;'
# >>> Expected: psql: error: FATAL:  password authentication failed for user "app"
```

## Access the Application

Once the deployment is running, use port-forwarding to access the application locally.

```bash
# 003.0 - Port-forward service to local machine
kubectl port-forward -n int-app-delta service/web-app-lua-db-internal 8080:80

# Open in browser:
# http://localhost:8080/
```
