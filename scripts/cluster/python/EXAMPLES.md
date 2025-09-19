# Examples

This "documentation" contains all user generation calls necessary for the project in the context of the RKE2 staging cluster for paligo.com/en and mpowr-it operational users as well as testing calls to the cluster using these kubeconfigs (x509 authentication certificates)

```bash

#
# create + verify new user certificate (valid for 365 days = maximum)
# --
python3 create-x509.py \
  --user mpowr-it--patrick \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify

python3 create-x509.py \
  --user mpowr-it--holger \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify

python3 create-x509.py \
  --user mpowr-it--ralf \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify


# Max Lorenz (mlo@paligo.com)
python3 create-x509.py \
  --user paligo-com--max \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify

# Erik Eisold (eei@paligo.com)
python3 create-x509.py \
  --user paligo-com--erik \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify

# Sascha Seyfert (sse@paligo.com)
python3 create-x509.py \
  --user paligo-com--sascha \
  --output-dir ./export \
  --expire-profile maximum \
  --role cluster-admin \
  --verify

#
# test kubeconfig using kubectl and direct config-file set
# --
KUBECONFIG=./export/mpowr-it--patrick/mpowr-it--patrick-kubeconfig.yaml kubectl get nodes
KUBECONFIG=./export/mpowr-it--holger/mpowr-it--holger-kubeconfig.yaml kubectl get nodes
KUBECONFIG=./export/mpowr-it--ralf/mpowr-it--ralf-kubeconfig.yaml kubectl get nodes

KUBECONFIG=./export/paligo-com--max/paligo-com--max-kubeconfig.yaml kubectl get nodes
KUBECONFIG=./export/paligo-com--erik/paligo-com--erik-kubeconfig.yaml kubectl get nodes
KUBECONFIG=./export/paligo-com--sascha/paligo-com--sascha-kubeconfig.yaml kubectl get nodes

```
---

## Author & License

- © 2025 MPOWR-IT GmbH
- Maintained by: patrick@mpowr.it, ralf@mpowr.it
- Version: 1.0.0-RC1
- License: Internal Use Only