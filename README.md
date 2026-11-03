# DevOps and Claim Processing Assignments

This repository contains a Celery/Redis task notifier with a single-page frontend and a separate LangGraph-based PDF claim extraction API. Docker Compose runs the services locally; Terraform and GitHub Actions provide an AWS deployment path.

## Run locally

### Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose v2
- Git

### Start the task notifier

Clone the repository and enter its directory:

```sh
git clone https://github.com/Teja2759/devops-assignment.git
cd devops-assignment
```

Create the local environment file and build/start the backend, Celery worker, and Redis:

```sh
cp .env.example .env
docker compose build
docker compose up -d
```

Open <http://localhost:8000>, enter an email address, and choose **Send notification**. The page submits a task and polls its status until it completes or fails. The API health check is at <http://localhost:8000/health/>.

Check running containers and follow logs:

```sh
docker compose ps
docker compose logs -f backend worker
docker compose logs -f redis
```

Stop the containers while preserving Redis data:

```sh
docker compose down
```

To also delete the local Redis data volume:

```sh
docker compose down -v
```

Do not commit `.env`; local settings and optional credentials belong there.

### Run the optional claim-processing API

Set your authorized `OPENAI_API_KEY` in `.env`, then start the claims API:

```sh
docker compose up --build -d claims-api
```

Open <http://localhost:8001/docs> for its API documentation. The PDF upload endpoint is `POST /api/process`. See [claims_pipeline/README.md](claims_pipeline/README.md) for request details and processing behavior. Claim contents are sent to the configured model for extraction, so only process documents you are authorized to share with that provider.

### Run tests

With Python and the packages in `requirements.txt` installed:

```sh
python -m unittest discover -s tests -v
```

## AWS deployment

The AWS deployment uses Terraform to provision the network, ECR, ECS Fargate services, ElastiCache Redis, Secrets Manager, CloudWatch logs, and GitHub OIDC deployment role. GitHub Actions tests pull requests; pushes to the configured branches build and deploy the app.

Follow [instructions.md](instructions.md) for AWS prerequisites, Terraform state setup, deployment configuration, monitoring, and teardown. Review AWS costs before applying. See [architecture.md](architecture.md) for the resource diagram and [journey.md](journey.md) for implementation decisions and limitations.

## Main components

- `backend/` and `frontend/`: FastAPI task API, Celery task, and browser UI
- `docker-compose.yml` and `Dockerfile`: local services and container image
- `infra/terraform/`: AWS application infrastructure
- `infra/state/`: Terraform state bucket bootstrap
- `.github/workflows/deploy.yml`: test, build, and ECS deployment workflow
- `claims_pipeline/`: independent PDF claim-processing API and workflow
- `tests/`: offline API and workflow tests
