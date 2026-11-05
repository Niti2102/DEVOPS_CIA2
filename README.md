# Simple Python CI/CD Demo

This project demonstrates:

```text
Git push -> GitHub Actions -> Python tests -> Docker image -> GHCR -> Azure AKS -> public URL
```

The single-file Flask application is a simple task manager. It provides:

- `/` - browser task manager page
- `/health` - Kubernetes health check
- `/api/tasks` - task list API
- `/api/version` - deployment information

The demo uses one Kubernetes replica because tasks are stored in application memory. This keeps the project simple and ensures add, complete, and delete operations use the same task list. A production version would use a database and multiple replicas.

## Required files

- `app.py` - Flask application
- `requirements.txt` - Python dependencies
- `tests/test_app.py` - automated tests
- `Dockerfile` - container image definition
- `.github/workflows/ci-cd.yml` - CI/CD pipeline
- `k8s/` - Kubernetes deployment, service, namespace, and Kustomize files

## Run locally

Requirements: Python 3.12+ and Docker Desktop.

```powershell
cd "E:\OneDrive - Shiv Nadar University - Chennai\Pictures\devops\DevOps-Cia-2"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python app.py
```

Open http://localhost:8081/. Kubernetes still uses port 8080 inside the container.

## Build and run with Docker

```powershell
docker build -t cicd-demo:local .
docker run --rm -p 8080:8080 cicd-demo:local
```

## Azure deployment

The workflow in [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs for every push to `main`:

1. Checks out the source code.
2. Installs Python 3.12 and project dependencies.
3. Runs the pytest unit tests.
4. Builds and tags a Docker image with the Git commit SHA.
5. Pushes the image to GitHub Container Registry.
6. Logs in to Azure using GitHub OIDC.
7. Updates the image in Azure Kubernetes Service.
8. Waits for the rollout and checks `/health`.

No Maven, Java, Gradle, or Ansible is used.

Add these repository variables under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | Entra application client ID |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Resource group containing AKS |
| `AZURE_AKS_CLUSTER_NAME` | AKS cluster name |

After deployment, find the public endpoint with:

```powershell
kubectl get service cicd-demo -n cicd-demo
```

For the redeployment demonstration, change the heading or sample task in `app.py`, commit, and push to `main`. The same public URL will show the updated task manager after the new image is deployed.
