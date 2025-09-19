# Installation Walkthrough Part 2

This walkthrough provides the steps to integrate HashiCorp Vault with the External Secrets Operator (ESO).
It covers installation of Vault in dev mode, configuration of Kubernetes authentication,
deployment of the workshop stack, and validation checks with PostgreSQL.

## Walkthrough Prerequisites

To follow this workshop, participants need access to a running Kubernetes cluster (minimum version **1.32.x**).
This can be set up locally using lightweight solutions such as Rancher Desktop, Docker Desktop, OrbStack, or kind.

Here are some resources to help you get started quickly:
- [Rancher Desktop Setup Guide](https://docs.rancherdesktop.io/getting-started/installation/)
- [Docker Desktop with Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [OrbStack Kubernetes Docs](https://orbstack.dev/docs/kubernetes)
- [kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/docs/user/quick-start/)

> **Note**: In this workshop example, Vault is installed in **dev mode**.  
> This is **not suitable for production** but simplifies the setup (no unseal procedure required).

## Preparations

Before deploying your application stack, ensure the required operators are installed into the cluster.
We use Helm charts for quick installation of Vault, CloudNativePG, External Secrets Operator,
and the Stakater Reloader.

```bash
# 000.0 - Create operator + vault namespaces
kubectl create namespace int-operators
kubectl create namespace int-vault

# 000.1 - Init helm charts
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo add external-secrets https://charts.external-secrets.io
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo add stakater https://stakater.github.io/stakater-charts
helm repo update

# 000.2 - Quick install Vault (dev mode + UI, no injector)
helm upgrade --install vault hashicorp/vault --namespace int-vault --set "server.dev.enabled=true" --set "ui.enabled=true" --set "injector.enabled=false"

# 000.3 - Quick install PostgreSQL operator (CloudNativePG)
helm upgrade --install cnpg cnpg/cloudnative-pg --namespace int-operators
  
# 000.4 - Quick install External Secrets Operator (incl. CRDs)
helm upgrade --install external-secrets external-secrets/external-secrets --namespace int-operators --set installCRDs=true

# 000.5 - Quick install Reloader (handles config/secret updates)  
helm upgrade --install reloader stakater/reloader --namespace int-operators
```

## Check Prerequisites

After installation, confirm that the CustomResourceDefinitions (CRDs) required by ESO
are available in the cluster.

```bash
# 001.0 - Check secret operator CRDs
kubectl get crds | egrep 'externalsecrets.external-secrets.io|secretstores.external-secrets.io|clustersecretstores.external-secrets.io|pushsecrets.external-secrets.io'
```

## Workshop Stack

The full workshop stack is managed using Kustomize. Apply the manifests from your local repository root to deploy
all components into the target namespace.

The repository layout for Part 2:

```
part-0/
├─ kustomization.yaml
├─ 000-preflight.yaml    # namespace, labels
├─ 105-secretstore-vault # hc-vault secret-store specs
├─ 110-external-secret   # external-secret mapping (username/password/etc.)
└─ 100-pgsql.yaml        # CNPG single-instance, uses the static secret
```

```bash
# 002.0 - Apply manifests
kubectl apply -k .

# optional alternatives
# kubectl apply -k . --prune
# kubectl replace -k . --force
```

## Initialize Vault

```bash
# 003.0 - Port-forward the Vault service
kubectl -n int-vault port-forward svc/vault 8200:8200

# 003.1 - Configure local environment for Vault CLI
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root"

# 003.2 - Verify Vault status
vault status

# 003.3 - Enable KV v2 secrets engine at path "kv-beta"
vault secrets enable -path=kv-beta kv-v2
```

## Configure Kubernetes Auth in Vault

```bash
# 004.0 - Prepare reviewer SA with TokenReview rights (system:auth-delegator)
kubectl create sa vault-reviewer -n int-operators
kubectl create clusterrolebinding vault-reviewer-binding \
        --clusterrole=system:auth-delegator \
        --serviceaccount=int-operators:vault-reviewer

# 004.1 - Extract reviewer token, CA cert, and API endpoint
REVIEWER_JWT="$(kubectl -n int-operators create token vault-reviewer)"
KUBE_CA="$(kubectl -n kube-system get cm kube-root-ca.crt -o jsonpath='{.data.ca\.crt}')"
KUBE_HOST="https://kubernetes.default.svc:443"

# 004.2 - Enable Kubernetes auth in Vault (idempotent)
vault auth enable kubernetes || true

# 004.3 - Configure the Kubernetes auth method
vault write auth/kubernetes/config \
      token_reviewer_jwt="$REVIEWER_JWT" \
      kubernetes_host="$KUBE_HOST" \
      kubernetes_ca_cert="$KUBE_CA" \
      issuer="https://kubernetes.default.svc.cluster.local"

# 004.4 - Define policy allowing ESO to read pgsql secret path
vault policy write eso-beta - <<'HCL'
path "kv-beta/data/app/config" {
  capabilities = ["read"]
}
HCL

# 004.5 - Bind policy to ESO ServiceAccount in ns int-app-beta
vault write auth/kubernetes/role/eso-beta \
      bound_service_account_names=eso-vault \
      bound_service_account_namespaces=int-app-beta \
      audience="https://kubernetes.default.svc.cluster.local" \
      policies=eso-beta \
      ttl=1h
```

## Insert PostgreSQL Credentials into Vault

```bash
# 005.0 - Store pgsql demo credentials (and further values) in Vault
vault kv put kv-beta/app/config \
      username=app \
      password='S3cur3-Pa55w0rd!' \ 
      database=app \
      host=beta-pg-rw.int-app-beta.svc.cluster.local \ 
      port=5432
```

## Check & Evaluate

With the stack deployed, we can validate the setup by checking generated secrets and verifying database connectivity.

```bash
# 006.0 - Check pgsql cluster state
kubectl -n int-app-beta get cluster beta-pg
kubectl -n int-app-beta get pods -l cnpg.io/cluster=beta-pg

# 006.1 - Check ESO resources
kubectl -n int-app-beta get externalsecret,secretstore

# 006.2 - Inspect generated K8s secret for pgsql
kubectl -n int-app-beta get secret beta-pg-app -o yaml

# 006.3 - Decode the complete secret object
kubectl -n int-app-beta get secret beta-pg-app   -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'

# 006.4 - Export DB connection string from Secret
unset DB_URI; export DB_URI="$(kubectl -n int-app-beta get secret beta-pg-app -o jsonpath='{.data.uri}' | base64 -d)"; echo "$DB_URI" 
# >>> Expected: postgresql://app:<password>@beta-pg-rw.int-app-beta.svc.cluster.local:5432/app

# 006.5 - Positive Test: valid credentials (connect inside CNPG pod)
kubectl -n int-app-beta exec -it beta-pg-1 -- psql "$DB_URI" -At -c 'select current_user,current_database();' 
# >>> Expected: app|app

# 006.6 - Negative Test: invalid password
BAD_URI="$(printf '%s' "$DB_URI" | sed -E 's#(postgresql://[^:]+:)[^@]+#\1WRONG#')"; echo "$BAD_URI"
kubectl -n int-app-beta exec -it beta-pg-1 -- psql "$BAD_URI" -c 'select 1;' 
# >>> Expected: psql: error: FATAL:  password authentication failed for user "app"
```

---

This completes the Vault integration walkthrough.  
At this point, the cluster has CNPG managing PostgreSQL, ESO syncing secrets from Vault,  
and Reloader ready to refresh application pods when configuration or credentials change.
