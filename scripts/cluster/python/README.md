# create-x509.py

Kubernetes x509 Certificate Generator via Kubernetes CSR API

Generates a key and CSR, submits it to Kubernetes, approves it, fetches the signed certificate, creates a base64-embedded kubeconfig, applies a ClusterRoleBinding, and verifies certificate/key integrity.

---

## Features

- CSR-based Kubernetes-native certificate flow
- Fully automated CSR submit, approve & fetch
- Embedded `kubeconfig` output (base64 encoded)
- Optional certificate/key modulus verification
- Optional expiration profile selection
- Automatic ClusterRoleBinding (default: cluster-admin)
- Safe cleanup via `--delete`

---

## Requirements

- Python 3.8+
- `kubectl` in PATH with sufficient RBAC rights
- `openssl` installed and callable
- Kubernetes CSR approval allowed

---

## Usage

### Create certificate and kubeconfig

```bash
python3 create-x509-csr.py \
  --user mpowr-it--patrick \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify
```

### Verify modulus (embedded cert vs private key)

```bash
openssl x509 -noout -modulus -in export/mpowr-it--patrick/mpowr-it--patrick.crt | openssl md5
openssl rsa  -noout -modulus -in export/mpowr-it--patrick/mpowr-it--patrick.key | openssl md5
```

### Delete CSR, ClusterRoleBinding & local files

```bash
python3 create-x509-csr.py \
  --user mpowr-it--patrick \
  --output-dir ./export \
  --delete
```

---

## Expiration Profiles

| Profile   | Duration               |
|-----------|------------------------|
| `short`   | 1 day (86,400s)        |
| `default` | 7 days (604,800s)      |
| `long`    | 30 days (2,592,000s)   |
| `maximum` | 365 days (31,536,000s) |

You can also override directly using `--expire <seconds>`.

---

## Output Structure

```
export/mpowr-it--patrick/
├── mpowr-it--patrick.key
├── mpowr-it--patrick.csr
├── mpowr-it--patrick.crt
├── mpowr-it--patrick-csr.yaml
├── mpowr-it--patrick-crb.yaml
├── mpowr-it--patrick-kubeconfig.yaml
```

---

## Author & License

- © 2025 MPOWR-IT GmbH
- Maintained by: patrick@mpowr.it, ralf@mpowr.it
- Version: 1.0.0-RC1
- License: Internal Use Only
