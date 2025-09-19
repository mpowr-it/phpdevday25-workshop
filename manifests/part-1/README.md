# Installation Walkthrough Part 1

This walkthrough provides the basic steps to set up the core operators and components needed for the workshop.
It covers installation of the required controllers, verification of prerequisites, deployment of the workshop stack,
and basic validation checks with PostgreSQL.

## Walkthrough Prerequisites

To follow this workshop, participants need access to a running Kubernetes cluster (minimum version **1.32.x**).
This can be set up locally using lightweight solutions such as Rancher Desktop, Docker Desktop, OrbStack, or kind.

Here are some resources to help you get started quickly:
- [Rancher Desktop Setup Guide](https://docs.rancherdesktop.io/getting-started/installation/)
- [Docker Desktop with Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [OrbStack Kubernetes Docs](https://orbstack.dev/docs/kubernetes)
- [kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/docs/user/quick-start/)

> **Note**: In this workshop example, an **AWS API key/secret pair** will be provided.
> These credentials are **time-limited (24h validity)** and scoped to a single object in AWS Secrets Manager.
> They only grant access to the data set used for the PostgreSQL cluster (credentials, host URI, etc.).

## Preparations

Before deploying your application stack, ensure the required operators are installed into the cluster.
We use Helm charts for quick installation of the CloudNativePG operator, External Secrets Operator,
and the Stakater Reloader.

```bash
# 000.0 - Create operator namespace
kubectl create namespace int-operators

# 000.1 - Init helm charts
helm repo add external-secrets https://charts.external-secrets.io
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo add stakater https://stakater.github.io/stakater-charts
helm repo update

# 000.2 - Quick install PostgreSQL operator (CloudNativePG)
helm upgrade --install cnpg cnpg/cloudnative-pg --namespace int-operators
  
# 000.3 - Quick install External Secrets Operator (incl. CRDs)
helm upgrade --install external-secrets external-secrets/external-secrets --namespace int-operators --set installCRDs=true

# 000.4 - Quick install Reloader (handles config/secret updates)  
helm upgrade --install reloader stakater/reloader --namespace int-operators
```

## Check Prerequisites

After installation, confirm that the CustomResourceDefinitions (CRDs) required by the External Secrets Operator
are available in the cluster.

```bash
# 001.0 - Check secret operator CRDs
kubectl get crds | egrep 'externalsecrets.external-secrets.io|secretstores.external-secrets.io|clustersecretstores.external-secrets.io|pushsecrets.external-secrets.io'
```

## Payload Structure

The following structure represents the initial security object as the basis of the AWS key for further use within the External Secret Manager for our cluster and contains all the important information needed to provide the PostgreSQL cluster with a suitable secret.

```json
{
  "username": "app",
  "password": "S3cur3-Pa55w0rd!",
  "database": "app",
  "host": "alpha-pg-rw.int-app-alpha.svc.cluster.local",
  "port": 5432
}
```

## Workshop Stack

The full workshop stack is managed using Kustomize. Apply the manifests from your local repository root to deploy
all components into the target namespace.

The repository layout for Part 1:

```
part-0/
├─ kustomization.yaml
├─ 000-preflight.yaml              # namespace, labels
├─ 105-secretstore-aws-static.yaml # aws secret-store specs
├─ 110-external-secret             # external-secret mapping (username/password/etc.)
└─ 100-pgsql.yaml                  # CNPG single-instance, uses the static secret
```

```bash
# 002.0 - Apply manifests
kubectl apply -k .

# optional alternatives
# kubectl apply -k . --prune
# kubectl replace -k . --force
```

## Check & Evaluate

With the stack deployed, we can validate the setup by checking generated secrets and verifying database connectivity.
These checks ensure that ESO has synced credentials correctly and that CNPG is updating the database user accordingly.

```bash
# 003.0 - Inspect auto generated secrets for pgsql
kubectl -n int-app-alpha get secret alpha-pg-app -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'

# 003.1 - Test the Postgres Connection (using CNPG + ESO secret)

# 003.2 - Export the connection string into a local env variable
unset DB_URI; export DB_URI="$(kubectl -n int-app-alpha get secret alpha-pg-app -o jsonpath='{.data.uri}' | base64 -d)"; echo "$DB_URI" 
# >>> Expected: postgresql://app:<password>@alpha-pg-rw.int-app-alpha.svc.cluster.local:5432/app

# 003.3 - Positive Test: valid credentials (connect inside CNPG pod)
kubectl -n int-app-alpha exec -it alpha-pg-1 -- psql "$DB_URI" -At -c 'select current_user,current_database();' 
# >>> Expected: app|app

# 003.4 - Negative Test: invalid password
BAD_URI="$(printf '%s' "$DB_URI" | sed -E 's#(postgresql://[^:]+:)[^@]+#\1WRONG#')"; echo "$BAD_URI"
kubectl -n int-app-alpha exec -it alpha-pg-1 -- psql "$BAD_URI" -c 'select 1;' 
# >>> Expected: psql: error: FATAL:  password authentication failed for user "app"
```

## Rotation Demo

To simulate a secret rotation with AWS-Secret-Manager:

### New Secret-Object (Example)

```json
{
  "username": "app",
  "password": "S3cur3-Pa55w0rd123",
  "database": "app",
  "host": "alpha-pg-rw.int-app-alpha.svc.cluster.local",
  "port": 5432,
  "uri": "postgresql://app:S3cur3-Pa55w0rd123@alpha-pg-rw.int-app-alpha.svc.cluster.local:5432/app",
  "jdbc-uri": "jdbc:postgresql://alpha-pg-rw.int-app-alpha.svc.cluster.local:5432/app?user=app&password=S3cur3-Pa55w0rd123"
}
```

```bash
# 007.0 - In AWS Secret-Manager, change the password-data inside the JSON (e.g. S3cur3-Pa55w0rd! → N3w-Pw!2025), save the item.
#         Note: Do not forget to adjust the entire object, including the URI and the JDBC-URI entry!

# 007.1 - Force reconcile of this ExternalSecret
kubectl -n int-app-alpha annotate externalsecret alpha-pg-app-es \
  'reconcile.external-secrets.io/requested-at='$(date +%s) --overwrite

# 007.2 - Verify secret-object got updated in Kubernetes
kubectl -n int-app-alpha get secret alpha-pg-app -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'
```

---

This completes the initial installation and validation steps.  
At this point, the cluster has CNPG managing PostgreSQL, ESO syncing secrets from AWS Secrets Manager,
and Reloader ready to refresh application pods when configuration or credentials change.
