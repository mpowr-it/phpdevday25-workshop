# PHPDevDay 2025, MPOWR-IT Workshop

## Modern Secret-Management in Kubernetes

This repository contains the materials for the **Kubernetes Secrets & External Secrets Workshop** at PHPDevDay 2025.  
The workshop is divided into multiple parts, each provided in its own subfolder (`manifests/part-0` to `manifests/part-4`).  
Each part comes with its own README containing specific instructions and exercises.

---

## Prerequisites

### Devbox Environment
For a consistent development setup we use [Devbox](https://www.jetify.com/devbox).

Install Devbox (Linux/macOS):
```bash
curl -fsSL https://get.jetify.com/devbox | bash
```

Then start the project setup from the root of this repository:
```bash
devbox shell
```

Required packages and tools will be installed automatically based on `devbox.json`.

---

## Workshop Structure

- [Part 0 – Introduction & Basics](./manifests/part-0/README.md)
- [Part 1 – First Steps with Secrets](./manifests/part-1/README.md)
- [Part 2 – External Secrets Operator](./manifests/part-2/README.md)
- [Part 3 – Password Rotation & Vault Integration](./manifests/part-3/README.md)
- [Part 4 – OpenResty Lua App with Secret Handling](./manifests/part-4/README.md)

Additional code examples can be found in the [`examples`](./manifests/examples) folder.

---

## Additional Information

- [`CHANGELOG.md`](./CHANGELOG.md) – Project change log
- [`ISSUES.md`](./ISSUES.md) – Known issues and notes
- [`LICENSE`](./LICENSE) – License information

---

## Version

Current version: [`VERSION`](./VERSION)  
