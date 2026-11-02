# DevOps Assessment Assignment

A small FastAPI + Celery application that queues notification tasks through Redis. The same Docker image runs the API and worker as separate processes. Locally, Docker Compose runs Redis; in AWS, Terraform provisions ECS Fargate and managed ElastiCache Redis.

## Quick start

```sh
cp .env.example .env
docker compose up --build
```

Open <http://localhost:8000>, submit an email, and watch the task status update. Local run, logs, cloud deployment, and teardown steps are in [instructions.md](instructions.md).

## Components

- `backend/main.py`: FastAPI endpoints and frontend serving route
- `backend/worker.py`: Celery app and background task
- `frontend/index.html`: single-page task submission and polling UI
- `Dockerfile` and `docker-compose.yml`: local containerized stack
- `infra/terraform/`: AWS network, ECR, ECS Fargate, ElastiCache Redis, IAM, Secrets Manager, and CloudWatch resources
- `infra/state/`: encrypted, versioned S3 Terraform state bucket
- `.github/workflows/deploy.yml`: GitHub Actions build and ECS deployment using OIDC

See [architecture.md](architecture.md) for the cloud resource diagram and [journey.md](journey.md) for implementation decisions and production considerations.
