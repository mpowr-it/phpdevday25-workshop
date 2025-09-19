# Installation Walkthrough Part 0 — Static Kubernetes Secret

This walkthrough demonstrates the **baseline approach**: managing PostgreSQL credentials with a
plain Kubernetes Secret (no external secret manager).  
It mirrors the structure used later with ESO (AWS SM, Vault, 1Password) so that participants can compare
static vs. externalized secrets.

---

## Prerequisites

To follow this workshop, participants need access to a running Kubernetes cluster (minimum version **1.32.x**).  
This can be set up locally using lightweight solutions such as Rancher Desktop, Docker Desktop, OrbStack, or kind.

Here are some resources to help you get started quickly:
- [Rancher Desktop Setup Guide](https://docs.rancherdesktop.io/getting-started/installation/)
- [Docker Desktop with Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [OrbStack Kubernetes Docs](https://orbstack.dev/docs/kubernetes)
- [kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/docs/user/quick-start/)

---

## Preparations

Ensure the CloudNativePG operator is installed in your cluster (namespace `int-operators`).  
If not yet available, please follow the **Preparations** section from Part 1.

---

## Workshop Stack

The repository layout for Part 0:

```
part-0/
├─ kustomization.yaml
├─ 000-preflight.yaml      # namespace, labels
├─ 090-secret-static.yaml  # static k8s secret (username/password/etc.)
└─ 100-pgsql.yaml          # CNPG single-instance, uses the static secret
```

Apply the manifests with Kustomize:

```bash
kubectl apply -k ./part-0

# optional alternatives
# kubectl apply -k ./part-0 --prune
# kubectl replace -k ./part-0 --force
```

---

## Check & Evaluate

With the stack deployed, validate the generated services and DB connectivity (purely static secret).

```bash
# 001.0 - Check pgsql cluster state
kubectl -n int-app-zero get cluster zero-pg
kubectl -n int-app-zero get pods -l cnpg.io/cluster=zero-pg

# 001.1 - Inspect static secret (decode all keys)
kubectl -n int-app-zero get secret zero-pg-app \
  -o go-template='{{range $k,$v := .data}}{{printf "%s: %s\n" $k ($v | base64decode)}}{{end}}'

# 001.2 - Export the connection string from the Secret
unset DB_URI; export DB_URI="$(kubectl -n int-app-zero get secret zero-pg-app \
  -o jsonpath='{.data.uri}' | base64 -d)"; echo "$DB_URI"
# >>> Expected: postgresql://app:<password>@zero-pg-rw.int-app-zero.svc.cluster.local:5432/app

# 001.3 - Positive Test: valid credentials (inside CNPG pod)
kubectl -n int-app-zero exec -it zero-pg-1 -- \
  psql "$DB_URI" -At -c 'select current_user,current_database();'
# >>> Expected: app|app

# 001.4 - Negative Test: invalid password
BAD_URI="$(printf '%s' "$DB_URI" | sed -E 's#(postgresql://[^:]+:)[^@]+#\1WRONG#')"; echo "$BAD_URI"
kubectl -n int-app-zero exec -it zero-pg-1 -- \
  psql "$BAD_URI" -c 'select 1;'
# >>> Expected: psql: error: FATAL:  password authentication failed for user "app"
```

---

## Manual Secret Rotation (Static)

Unlike ESO-managed secrets, a static Secret requires manual updates when credentials change.
Here is how you can rotate the password manually:

```bash
# 002.0 - Edit the Secret and set a new password
kubectl -n int-app-zero edit secret zero-pg-app

# 002.1 - Alternatively, patch only the password field
NEWPW="N3w-Pw!2025"
kubectl -n int-app-zero patch secret zero-pg-app \
  --type merge \
  -p="{\"stringData\":{\"password\":\"$NEWPW\", \"uri\":\"postgresql://app:$NEWPW@zero-pg-rw.int-app-zero.svc.cluster.local:5432/app\"}}"

# 002.2 - Verify the Secret has been updated
kubectl -n int-app-zero get secret zero-pg-app -o jsonpath='{.data.password}' | base64 -d; echo

# 002.3 - Tell CNPG to reload credentials (it watches the Secret)
kubectl -n int-app-zero annotate secret zero-pg-app cnpg.io/reload=true --overwrite
```

> **Note**: In a real production scenario you would also need to update the actual Postgres role password inside the database.  
> CNPG supports this automatically when the target Secret is labeled with `cnpg.io/reload: "true"`.

---

## Notes (drop-in footer comments for YAMLs)

```yaml
#
# creationPolicy: Owner
#   Not used in Part 0 (no ESO). In later parts, ESO creates the target Secret if missing
#   and keeps its mapped keys in sync.
#
# deletionPolicy: Retain
#   Also an ESO setting. Keeps the Kubernetes Secret if the ExternalSecret is deleted.
#
# template.mergePolicy: Merge
#   ESO-only. Lets you add labels/annotations/keys later without hard-overwriting.
#
# dataFrom.extract
#   ESO-only. Pulls JSON properties 1:1 from the external provider (AWS/Vault/1Password).
#   CNPG can add its own keys in parallel; ESO won’t touch keys it doesn’t manage.
#
# cnpg.io/reload: "true"
#   CNPG reacts to password changes on the Secret and updates the DB role password
#   inside PostgreSQL (no custom SQL/Jobs required). Works for static and ESO-managed secrets.
#
```

---

This completes Part 0 — a static secret example.
From here, you can continue with Part 1 (AWS Secrets Manager) to see how ESO
externalizes this same pattern.
