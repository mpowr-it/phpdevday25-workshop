# Installation Walkthrough Part 3

This walkthrough demonstrates how to integrate **1Password** with the External Secrets Operator (ESO)
to manage PostgreSQL credentials in Kubernetes.  
It covers the setup of the operator stack, retrieval of values from 1Password,
validation of secret synchronization, and a demonstration of secret rotation.

## Walkthrough Prerequisites

To follow this workshop, participants need access to a running Kubernetes cluster (minimum version **1.32.x**).  
This can be set up locally using lightweight solutions such as Rancher Desktop, Docker Desktop, OrbStack, or kind.

Here are some resources to help you get started quickly:
- [Rancher Desktop Setup Guide](https://docs.rancherdesktop.io/getting-started/installation/)
- [Docker Desktop with Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [OrbStack Kubernetes Docs](https://orbstack.dev/docs/kubernetes)
- [kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/docs/user/quick-start/)

> **Note**: In this workshop example, a **1Password Service Account token** and a **vault reference** will be provided.  
> These credentials are **time-limited (24h validity)** and scoped to a **single vault item** in the company 1Password account.  
> They only grant **read-only access** to this object, which is why storing the token in GitLab CI for this workshop is acceptable.

## Preparations

Before deploying your application stack, ensure the required operators are installed into the cluster.  
We use Helm charts for quick installation of the CloudNativePG operator, External Secrets Operator,
and the Stakater Reloader.

```bash
# create operator namespace
kubectl create namespace int-operators

# init helm charts
helm repo add external-secrets https://charts.external-secrets.io
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo add stakater https://stakater.github.io/stakater-charts
helm repo update

# quick install pgsql operator
helm upgrade --install cnpg cnpg/cloudnative-pg --namespace int-operators

# quick install external secrets operator (incl. CRDs)
helm upgrade --install external-secrets external-secrets/external-secrets --namespace int-operators --set installCRDs=true

# quick install reloader operator (handles config/secret updates)  
helm upgrade --install reloader stakater/reloader --namespace int-operators
```

## Payload Structure

The following structure represents the initial security object as payload for our 1Passsord Secure-Notice for further use within the External Secret Manager for our cluster and contains all the important information needed to provide the PostgreSQL cluster with a suitable secret.

```json
{
  "username": "app",
  "password": "S3cur3-Pa55w0rd!",
  "database": "app",
  "host": "gamma-pg-rw.int-app-gamma.svc.cluster.local",
  "port": 5432,
  "uri": "postgresql://app:S3cur3-Pa55w0rd!@gamma-pg-rw.int-app-gamma.svc.cluster.local:5432/app",
  "jdbc-uri": "jdbc:postgresql://gamma-pg-rw.int-app-alpha.svc.cluster.local:5432/app?user=app&password=S3cur3-Pa55w0rd!"
}
```

## Check 1Password Vault Value

Verify that the `gamma-pg-clean` entry exists in the `workshop-gamma` vault and contains
the expected JSON fields (`username`, `password`, `database`, `host`, `port`).

```bash
op signin
op item get "gamma-pg-clean" --vault "workshop-gamma" --format json \
  | jq '.fields[] | {label, id, type, section: (.section.label // null)}'
```

## Workshop Stack

The full workshop stack is managed using Kustomize. Apply the manifests from your local repository root
to deploy all components into the target namespace.

The repository layout for Part 3:

```
part-0/
├─ kustomization.yaml
├─ 000-preflight.yaml  # namespace, labels
├─ 105-secretstore     # 1password secret-store specs
├─ 110-external-secret # external-secret mapping (username/password/etc.)
└─ 100-pgsql.yaml      # CNPG single-instance, uses the static secret
```

```bash
kubectl apply -k .

# optional alternatives
# kubectl apply -k . --prune
# kubectl replace -k . --force
```

## Check & Evaluate

With the stack deployed, we can validate the setup by checking generated secrets and verifying database connectivity.

```bash
# 006.0 - Check pgsql cluster state
kubectl -n int-app-gamma get cluster gamma-pg
kubectl -n int-app-gamma get pods -l cnpg.io/cluster=gamma-pg

# 006.1 - Check ESO resources
kubectl -n int-app-gamma get externalsecret,secretstore

# 006.2 - Inspect generated K8s secret for pgsql (already done)
kubectl -n int-app-gamma get secret gamma-pg-app \
  -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'

# 006.3 - Export DB connection string from Secret
unset DB_URI; export DB_URI="$(kubectl -n int-app-gamma get secret gamma-pg-app \
  -o jsonpath='{.data.uri}' | base64 -d)"; echo "$DB_URI"
# >>> Expected: postgresql://app:<password>@gamma-pg-rw.int-app-gamma.svc.cluster.local:5432/app

# 006.4 - Positive Test: valid credentials (connect inside CNPG pod)
kubectl -n int-app-gamma exec -it gamma-pg-1 -- \
  psql "$DB_URI" -At -c 'select current_user,current_database();'
# >>> Expected: app|app

# 006.5 - Negative Test: invalid password (try connecting with a bad password)
BAD_URI="$(printf '%s' "$DB_URI" | sed -E 's#(postgresql://[^:]+:)[^@]+#\1WRONG#')"; echo "$BAD_URI"
kubectl -n int-app-gamma exec -it gamma-pg-1 -- \
  psql "$BAD_URI" -c 'select 1;'
# >>> Expected: psql: error: FATAL:  password authentication failed for user "app"
```

## Rotation Demo

To simulate a secret rotation with 1Password:

### New Secret-Object (Example)

```json
{
  "username": "app",
  "password": "S3cur3-Pa55w0rd456",
  "database": "app",
  "host": "gamma-pg-rw.int-app-gamma.svc.cluster.local",
  "port": 5432
}
```

```bash
# 007.0 - In 1Password, change the password inside the JSON (e.g. S3cur3-Pa55w0rd! → N3w-Pw!2025), save the item.
#         Note: Do not forget to adjust the entire object, including the URI and the JDBC-URI entry!

# 007.1 - Force reconcile of this ExternalSecret
kubectl -n int-app-gamma annotate externalsecret gamma-pg-app-es \
  'reconcile.external-secrets.io/requested-at='$(date +%s) --overwrite

# 007.2 - Verify secret got updated in Kubernetes
kubectl -n int-app-gamma get secret gamma-pg-app -o jsonpath='{.data.password}' | base64 -d; echo
```

---

This completes the third installation and validation walkthrough.  
At this point, the cluster has CNPG managing PostgreSQL, ESO syncing secrets from **1Password**,  
and Reloader ready to refresh application pods when configuration or credentials change.
