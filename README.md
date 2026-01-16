### 🔍 Deployment Workflow
* The deploy.py script automates several complex manual steps:
  * Project Setup: Sets the active GCP project and compute region.
  * Docker Build: Builds the image using Dockerfile.detached and passes DEPLOY_SERVER_PORT as a build argument.
  * Registry Push: Tags the image for asia.gcr.io and pushes it to the Google Container Registry.
  * Cloud Run Deployment: Deploys the service with the --allow-unauthenticated flag to allow public access.
  * IAM Policy Binding: Automatically adds the roles/run.invoker role to allUsers to finalize public accessibility.

### - Environment Configuration
* The script relies on a .env file located in the project root. Create a file named .env and include the following variables:
  
```ini
# ==========================================
# Google Cloud Configuration (Examples)
# ==========================================

# GCP Project ID (Required)
GCP_PROJECT_ID=clear-tooling-...

# Deployment Region (LOCATION maps to REGION in script)
LOCATION=asia-northeast3

# ==========================================
# Server & Image Settings (Examples)
# ==========================================

# Server Port
DEPLOY_SERVER_PORT=8866

# Docker Image & Cloud Run Service Name
IMAGE_NAME=DOCKER_IMAGE_NAME
SERVICE_NAME=test-server

# Google Container Registry Host
GCR_HOST=asia.gcr.io

# ==========================================
# Authentication (Examples)
# ==========================================

# Path to your Service Account JSON key file
GOOGLE_APPLICATION_CREDENTIALS=./clear-tooling-....json
```

---

## Author

#### - [LinkedIn](https://www.linkedin.com/in/taeyong-kong-016bb2154)

#### - [Blog URL](https://blog.naver.com/qbxlvnf11)

#### - Email: qbxlvnf11@google.com, qbxlvnf11@naver.com


