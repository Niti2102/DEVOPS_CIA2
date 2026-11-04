# Technical Report: End-to-End Cloud CI/CD Pipeline Design

## 1. Problem definition

Modern software teams often follow manual release workflows that involve building the Java artifact locally, running tests, creating containers, and deploying the application by hand. This process is both slow and error-prone. It is difficult to guarantee consistent deployments and the same code version reaching production across different environments. The challenge is to automate the whole software delivery lifecycle so that any validated code change can be delivered to a cloud-hosted environment without manual intervention.

The project requirement is to create a real CI/CD pipeline for a Java web application using a cloud provider, Git, Maven, Docker, and Kubernetes. The solution should include automated build and test stages, code checkout, image publishing, and deployment to a managed Kubernetes cluster. It should also produce supporting deployment files and documentation.

## 2. Architecture overview

The application is a lightweight Spring Boot service that exposes a responsive public landing page, health endpoint, and version endpoint. The pipeline is implemented with GitHub Actions and runs when code is pushed to the main branch. The toolchain includes Java 17 for compilation, Maven for dependency management and test execution, Docker for containerization, and Kubernetes for orchestration.

The deployment target is Azure Kubernetes Service (AKS), which is a managed Kubernetes service in Microsoft Azure. The deployment workflow authenticates to Azure using GitHub OIDC federation, updates the cluster context, and applies the Kubernetes manifests. This avoids keeping a long-lived Azure client secret in GitHub. The service exposes the app through a Load Balancer so it can be accessed externally.

```mermaid
flowchart LR
    Dev[Developer pushes to main] --> Repo[GitHub repository]
    Repo --> Actions[GitHub Actions]
    Actions --> Maven[Maven build and tests]
    Maven --> Image[Docker image]
    Image --> GHCR[GitHub Container Registry]
    Actions -->|OIDC| Azure[Azure identity]
    GHCR --> AKS[AKS deployment]
    Azure --> AKS
    AKS --> Service[LoadBalancer service]
    Service --> Browser[Public HTTP endpoint]
```

## 3. Tools selected and justification

- GitHub: provides source control and CI trigger events.
- Java 17 and Maven: standard build and dependency tooling for Java applications.
- Spring Boot: reduces boilerplate and gives a clean REST API framework.
- Docker: ensures the application runs consistently across environments.
- Kubernetes: provides container orchestration, scaling, and health checks.
- Azure AKS: managed Kubernetes reduces administration overhead and is suitable for cloud deployment.
- GitHub Actions: suitable, low-overhead CI/CD platform integrated with GitHub.
- Gitleaks: detects accidentally committed secrets before build and deployment.
- Ansible: useful for repeatable deployment automation and infrastructure configuration tasks.

This toolset is highly compatible with the requirements and is widely used in production-ready DevOps workflows.

## 4. CI/CD pipeline stages

The pipeline is configured in `.github/workflows/ci-cd.yml` and includes the following stages:

1. Checkout source code.
2. Scan the full Git history for secrets with Gitleaks.
3. Set up the Java environment.
4. Run unit tests with Maven.
5. Package the application as a JAR.
6. Build Docker image.
7. Push image to GitHub Container Registry.
8. Authenticate to Azure.
9. Apply Kubernetes manifests.
10. Wait for rollout completion.
11. Verify the new version is running.

The secret-scan job is a required dependency of the build job, so no image is published and no deployment occurs if Gitleaks detects a secret. The later stages are also ordered so that a failed test prevents deployment. This is a core DevOps principle: only a security-checked and validated build should be deployed.

## 5. Cloud resources and deployment approach

The deployment architecture includes the following components:

- GitHub repository: source of truth for application code and workflow definitions.
- GitHub Container Registry: stores the built Docker image.
- Azure Resource Group: container for AKS resources.
- Azure AKS cluster: hosts the application containers.
- Kubernetes Deployment: defines the desired number of pods.
- Kubernetes Service: exposes the application to external traffic using a LoadBalancer.

The application is deployed in the `cicd-demo` namespace. The deployment uses two replicas for resilience and declares readiness and liveness probes so Kubernetes only sends traffic to healthy containers. The manifest repository is versioned along with the app code, making the deployment state reproducible.

The live cluster is `devops-cia2-aks` in the `new-devops-cia2-rg` resource group in Central India. It uses AKS Free control-plane tier and one `Standard_D2s_v4` worker node; the application runs two replicas on that node. The public service endpoint is `http://4.187.190.194/`. Although the control-plane tier is Free, the worker VM, disk, and public networking are billable and consume Azure for Students credit.

## 6. Implementation details

The repository contains these key files:

- `pom.xml`: Maven project definition and Spring Boot configuration.
- `src/main/java/com/example/cicd/CicdDemoApplication.java`: main Spring Boot entry point.
- `src/main/java/com/example/cicd/AppController.java`: REST endpoints.
- `src/test/java/com/example/cicd/AppControllerTest.java`: unit and integration-style tests.
- `Dockerfile`: multi-stage build for a Java container image.
- `k8s/deployment.yaml`: Kubernetes deployment definition.
- `k8s/service.yaml`: external service definition.
- `ansible/playbook.yml`: example deployment automation script.
- `.github/workflows/ci-cd.yml`: CI/CD workflow definition.
- `src/main/resources/static/index.html`: responsive landing page served at the public root URL.

The landing page displays the deployment status and retrieves the current version and environment from the live APIs. The version endpoint also helps validate that the desired code change is being served by the running cluster. This makes the demonstration easy to understand during a live demo.

## 7. Testing and verification evidence

The application has automated checks for the following behaviors:

- root endpoint serves the landing page
- health endpoint reports service health
- version endpoint returns the app version and metadata

These tests are executed during the GitHub Actions workflow before the Docker image is built. This ensures that broken code does not reach the registry or the cluster.

The local validation command used during development was:

```bash
mvn -B clean test
```

The test result was **3 tests, 0 failures, 0 errors**. The successful GitHub Actions run builds and publishes the image, authenticates to Azure using OIDC, and rolls out the deployment: [pipeline run](https://github.com/josondev/DevOps-Cia-2/actions/runs/41783174461).

The deployed endpoint returned `{"status":"UP","service":"cicd-demo"}` at `/health` and `{"app":"cicd-demo","version":"1.0.1","environment":"prod"}` at `/api/version`. The Kubernetes Deployment reported two of two replicas ready.

The pipeline now includes a Gitleaks full-history scan as its first required job. A successful scan is evidence that no supported secret pattern was detected in the repository history available to the workflow. Gitleaks complements, rather than replaces, Azure OIDC, least-privilege RBAC, and careful secret management.

## 8. Challenges and solutions

The Azure for Students subscription rejected the initially selected `Standard_D2s_v3` VM size, so the cluster was created with the subscription-allowed `Standard_D2s_v4` size instead. GitHub's OIDC subject for this repository includes immutable owner and repository IDs; using the older name-only subject caused authentication to fail. The federated credential was updated to match the actual token subject, after which Azure login succeeded. The first AKS deployment also required installing `kubelogin` on the GitHub runner for non-admin Azure RBAC authentication.

Another challenge is making Kubernetes deployment consistent. Using manifests stored in the repository and applying them in the GitHub workflow ensures the same configuration is used across environments and that updates are traceable.

## 9. Security considerations and limitations

Production systems should include the following measures:

- short-lived GitHub OIDC tokens instead of stored Azure client secrets
- Gitleaks secret scanning before image creation and deployment
- secret management via GitHub Secrets, Azure Key Vault, or Kubernetes Secrets
- image scanning and vulnerability analysis
- private registry access for production deployments (the training image is public to allow AKS pulls without a stored token)
- TLS/ingress configuration for public workloads
- RBAC restrictions for cluster access
- environment-specific configuration with configuration maps or secrets

The demo uses GitHub OIDC federation and namespace-scoped AKS write access for the pipeline identity; no long-lived Azure client secret is stored in GitHub. The repository, image, and HTTP endpoint are public. The cluster is a single-node training setup without TLS or production high availability, and active Azure resources continue to incur compute and networking charges.

## 10. Live demonstration plan

To demonstrate the workflow end-to-end, the following steps can be followed:

1. Change the API version or response and commit it to `main`.
2. Push the commit to GitHub.
3. Observe the GitHub Actions workflow automatically trigger.
4. Confirm Maven tests pass.
5. Confirm the Docker image is pushed to the registry.
6. Confirm the AKS deployment is updated.
7. Visit `http://4.187.190.194/` to view the deployed landing page and `http://4.187.190.194/api/version` to see the new version and `prod` profile.

For the completed demonstration, commit `5493557` changed the application version to `1.0.1`. Pipeline run [41783174461](https://github.com/josondev/DevOps-Cia-2/actions/runs/41783174461) passed, including the Gitleaks gate, published the image, and deployed it automatically. The live deployment is available at [http://4.187.190.194/](http://4.187.190.194/), with health at [http://4.187.190.194/health](http://4.187.190.194/health) and the deployed version at [http://4.187.190.194/api/version](http://4.187.190.194/api/version).

This proves that a code change can pass through the whole pipeline and appear in the running application automatically.

## 11. Conclusion

The implemented solution satisfies the assignment requirements by combining Git, Maven, Docker, Kubernetes, CI/CD automation, and cloud deployment. It is structured for real-world use, is easy to extend, and can be adapted to an Azure, AWS, or GCP deployment target. The result is an end-to-end, repeatable pipeline that demonstrates the value of automation in modern software delivery.
