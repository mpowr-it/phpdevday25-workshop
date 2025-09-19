#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create-x509-csr.py
-------------------
Kubernetes x509 Certificate Generator via Kubernetes CSR API
Generates key + CSR, submits to Kubernetes, approves CSR, fetches signed certificate, builds kubeconfig

(c) 2025 MPOWR-IT GmbH
Maintained by: patrick@mpowr.it, ralf@mpowr.it
"""

import os
import subprocess
import base64
import tempfile
import yaml
from pathlib import Path
from argparse import ArgumentParser

# Constants
COPYRIGHT = "MPOWR-IT GmbH"
VERSION = "1.0.0-RC1"
LOGO_FILE = "./meta/logo-v2.asc"

def print_cli_title():
    """Prints a CLI title with logo, copyright, and version information."""
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "r") as f:
            print(f.read())
    else:
        print("Kubernetes x509 User-Certificate Generator (CSR-based)")
    print(f"Copyright (c) {COPYRIGHT}")
    print(f"Version: {VERSION}")
    print(f"Maintainer: patrick.paechnatz@mpowr.it\n")

def run(cmd):
    subprocess.check_call(cmd, shell=True)

def get_output(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

def log(msg):
    print(f"[INFO] {msg}")

def create_key_and_csr(user: str, outdir: Path):
    key_path = outdir / f"{user}.key"
    csr_path = outdir / f"{user}.csr"

    log(f"Generating private key and CSR for user '{user}'")
    run(f"openssl genrsa -out {key_path} 4096")
    run(f"openssl req -new -key {key_path} -subj \"/CN={user}\" -out {csr_path}")
    return key_path, csr_path

def create_csr_yaml(user: str, csr_path: Path, expire_sec: int, outdir: Path) -> Path:
    yaml_path = outdir / f"{user}-csr.yaml"
    with open(csr_path, "rb") as f:
        csr_b64 = base64.b64encode(f.read()).decode()

    csr_obj = {
        "apiVersion": "certificates.k8s.io/v1",
        "kind": "CertificateSigningRequest",
        "metadata": {"name": user},
        "spec": {
            "groups": ["system:authenticated"],
            "request": csr_b64,
            "signerName": "kubernetes.io/kube-apiserver-client",
            "expirationSeconds": expire_sec,
            "usages": ["digital signature", "key encipherment", "client auth"]
        }
    }

    with open(yaml_path, "w") as f:
        yaml.safe_dump(csr_obj, f)
    return yaml_path

def submit_and_approve_csr(csr_yaml: Path, user: str):
    log("Deleting existing CSR (if any)")
    try:
        run(f"kubectl delete csr {user}")
    except subprocess.CalledProcessError:
        log("No existing CSR to delete (ok)")
    log("Submitting CSR to Kubernetes API")
    run(f"kubectl apply -f {csr_yaml}")
    log("Approving CSR")
    run(f"kubectl certificate approve {user}")

def fetch_certificate(user: str, outdir: Path) -> Path:
    cert_path = outdir / f"{user}.crt"
    log("Fetching signed certificate from Kubernetes API")
    cert_b64 = get_output(f"kubectl get csr {user} -o jsonpath='{{.status.certificate}}'")
    with open(cert_path, "wb") as f:
        f.write(base64.b64decode(cert_b64))
    return cert_path

def get_cluster_info():
    server = get_output("kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'").strip("'")
    ca_data = get_output("kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'")
    return server, ca_data

def create_kubeconfig(user: str, crt: Path, key: Path, server: str, ca_data: str, outdir: Path) -> Path:
    cert_data = base64.b64encode(crt.read_bytes()).decode()
    key_data = base64.b64encode(key.read_bytes()).decode()

    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{
            "name": "cluster",
            "cluster": {
                "server": server,
                "certificate-authority-data": ca_data
            }
        }],
        "users": [{
            "name": user,
            "user": {
                "client-certificate-data": cert_data,
                "client-key-data": key_data
            }
        }],
        "contexts": [{
            "name": f"{user}@cluster",
            "context": {
                "cluster": "cluster",
                "user": user
            }
        }],
        "current-context": f"{user}@cluster"
    }

    kubeconfig_path = outdir / f"{user}-kubeconfig.yaml"
    with open(kubeconfig_path, "w") as f:
        yaml.safe_dump(config, f)
    return kubeconfig_path



def create_cluster_role_binding(user: str, outdir: Path, role: str = "cluster-admin"):
    crb_path = outdir / f"{user}-crb.yaml"
    crb_yaml = f"""apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: crb-{user}
subjects:
  - kind: User
    name: {user}
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: {role}
  apiGroup: rbac.authorization.k8s.io
"""
    with open(crb_path, "w") as f:
        f.write(crb_yaml)
    run(f"kubectl apply -f {crb_path}")
    print(f"[✓] ClusterRoleBinding applied & written to: {crb_path}")


def verify_key_cert_pair(cert: Path, key: Path):
    def get_modulus(path: Path, is_key: bool = False):
        cmd = (
            f"openssl rsa -noout -modulus -in {path} | openssl md5"
            if is_key else
            f"openssl x509 -noout -modulus -in {path} | openssl md5"
        )
        return subprocess.check_output(cmd, shell=True).decode().strip()

    cert_hash = get_modulus(cert)
    key_hash = get_modulus(key, is_key=True)

    print("\n[VERIFY] Certificate Modulus:", cert_hash)
    print("[VERIFY] Private Key Modulus:", key_hash)
    if cert_hash == key_hash:
        print("✅ Cert/Key match.")
    else:
        print("❌ Cert/Key mismatch!")


def delete_user_cert_and_rbac(user: str, outdir: Path):
    log(f"Deleting Kubernetes CSR and RBAC for user: {user}")
    try:
        run(f"kubectl delete csr {user}")
    except subprocess.CalledProcessError:
        print(f"[WARN] CSR {user} not found or already deleted.")

    try:
        run(f"kubectl delete clusterrolebinding crb-{user}")
    except subprocess.CalledProcessError:
        print(f"[WARN] ClusterRoleBinding crb-{user} not found or already deleted.")

    user_dir = outdir / user
    if user_dir.exists():
        for file in user_dir.glob(f"{user}*"):
            try:
                file.unlink()
            except Exception as e:
                print(f"[WARN] Failed to delete {file}: {e}")

        user_dir.rmdir()
        print(f"[✓] Local files for user {user} removed.")
    else:
        print(f"[INFO] No local files found for user {user} in {user_dir}")


def resolve_expiration(profile: str, override: int = None) -> int:
    if override:
        return override
    profile_map = {
        "short": 86400,       # 1 day
        "default": 604800,    # 7 days
        "long": 2592000,      # 30 days
        "maximum": 31536000   # 365 days
    }
    return profile_map.get(profile, 604800)  # fallback = default


def main():
    print_cli_title()

    parser = ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Delete user CSR, CRB, and local files")
    parser.add_argument("--user", required=True, help="Username to include in the CN")
    parser.add_argument("--output-dir", default="./export", help="Output directory")
    parser.add_argument("--expire", type=int, default=None, help="Explicit expiration in seconds")
    parser.add_argument("--expire-profile", choices=["short", "default", "long", "maximum"], default="default", help="Predefined expiration profiles")
    parser.add_argument("--role", default="cluster-admin", help="ClusterRole name to bind")
    parser.add_argument("--verify", action="store_true", help="Verify that cert and key match after creation")
    args = parser.parse_args()

    if args.delete:
        delete_user_cert_and_rbac(args.user, Path(args.output_dir))
        return

    outdir = Path(args.output_dir) / args.user
    outdir.mkdir(parents=True, exist_ok=True)

    key, csr = create_key_and_csr(args.user, outdir)
    expiration = resolve_expiration(args.expire_profile, args.expire)
    csr_yaml = create_csr_yaml(args.user, csr, expiration, outdir)
    submit_and_approve_csr(csr_yaml, args.user)
    crt = fetch_certificate(args.user, outdir)
    server, ca_data = get_cluster_info()
    kubeconfig = create_kubeconfig(args.user, crt, key, server, ca_data, outdir)

    print(f"[✓] kubeconfig written to: {kubeconfig}")

    create_cluster_role_binding(args.user, outdir, args.role)

    if args.verify:
        verify_key_cert_pair(crt, key)


if __name__ == "__main__":
    main()
