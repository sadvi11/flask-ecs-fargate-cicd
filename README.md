# Flask ECS Fargate CI/CD

> Production-grade containerized API deployed on AWS ECS Fargate with fully automated CI/CD pipeline via GitHub Actions. Every push to `main` builds, pushes to ECR, and deploys to ECS automatically — zero manual steps.

**Live demo:** [https://flask-ecs-fargate-cicd.onrender.com/health](https://flask-ecs-fargate-cicd.onrender.com/health)


---

## What this project demonstrates

- Containerizing a Python Flask API with Docker (multi-platform `linux/amd64` build)
- Storing container images in Amazon ECR with versioned tags per commit SHA 
- Running containers serverlessly on AWS ECS Fargate — no EC2 instances to manage
- Automated CI/CD: GitHub Actions pipeline deploys on every push to `main`
- CloudWatch logging for production observability
- Security: AWS credentials stored as GitHub Secrets, never in code

---
 
## Architecture

📐 **[View full architecture diagram →](diagrams/ARCHITECTURE.md)**

mermaid
flowchart LR
  Dev(["Developer pushes code"])
  B["Build Docker image"]
  P["Push to ECR"]
  D["Deploy to ECS Fargate"]
  ECR["Amazon ECR"]
  ECS["ECS Fargate"]
  CW["CloudWatch"]
  Dev --> B --> P --> D
  P --> ECR
  D --> ECS
  ECS --> ECR
  ECS --> CW

 
## AWS services used

| Service | Purpose |
|---|---|
| Amazon ECR | Private container image registry |
| Amazon ECS Fargate | Serverless container runtime — no EC2 to manage |
| AWS IAM | Task execution role with least-privilege permissions |
| Amazon CloudWatch | Container logs at `/ecs/flask-ecs-fargate` |
| Amazon VPC | Network isolation with security groups |
| GitHub Actions | CI/CD pipeline — build, push, deploy on every commit |

---

## API endpoints

### Health check
```bash
GET /health
```
```json
{"service": "flask-ecs-fargate", "status": "healthy"}
```

### Home
```bash
GET /
```
```json
{"message": "Flask app running on ECS Fargate", "version": "1.0.0"}
```

### Calculate monthly payment
```bash
POST /calculate
Content-Type: application/json

{
  "principal": 500000,
  "annual_rate": 5.5,
  "years": 25
}
```
```json
{
  "annual_rate": 5.5,
  "monthly_payment": 3070.44,
  "principal": 500000,
  "total_payment": 921131.24,
  "years": 25
}
```

---

## CI/CD pipeline — how it works

The `.github/workflows/deploy.yml` pipeline runs on every push to `main`:

1. **Build** — Docker image built for `linux/amd64` (required for Fargate)
2. **Tag** — image tagged with Git commit SHA for traceability and rollback capability
3. **Push** — image pushed to Amazon ECR private registry
4. **Fetch** — current task definition pulled live from AWS (no hardcoded values in repo)
5. **Render** — new image URI injected into task definition
6. **Deploy** — ECS service updated with new task definition, waits for stability

---

## Project structure
flask-ecs-fargate-cicd/

├── app/

│   ├── app.py                  # Flask API

│   ├── requirements.txt        # Python dependencies

│   └── Dockerfile              # Multi-stage build for linux/amd64

├── .aws/

│   └── task-definition.json    # ECS task definition (ACCOUNT_ID placeholder)

├── .github/

│   └── workflows/

│       └── deploy.yml          # GitHub Actions CI/CD pipeline

└── README.md
---

## Security practices

- AWS credentials stored as GitHub Secrets — never in code or config files
- Account ID injected at pipeline runtime via `sed` — never committed to repo
- Task definition downloaded live from AWS during deployment — no stale configs
- IAM execution role follows least-privilege — only ECR pull and CloudWatch write
- Security group restricts inbound to port 8080 only

---

## How to deploy this yourself

**Prerequisites:** AWS CLI configured, Docker installed, GitHub repo with secrets set.

**1. Create ECR repository:**
```bash
aws ecr create-repository \
  --repository-name flask-ecs-fargate \
  --region ca-central-1
```

**2. Create ECS cluster:**
```bash
aws ecs create-cluster \
  --cluster-name flask-ecs-cluster \
  --region ca-central-1
```

**3. Create CloudWatch log group:**
```bash
aws logs create-log-group \
  --log-group-name /ecs/flask-ecs-fargate \
  --region ca-central-1
```

**4. Add GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`

**5. Push to main — pipeline runs automatically.**

---

## Key technical decisions

**Why ECS Fargate over EC2?**
No server management. AWS handles the underlying infrastructure — patching, scaling, availability. You define CPU and memory at the task level and pay only for what runs.

**Why commit SHA as image tag?**
Every deployment is traceable to an exact commit. Rolling back means redeploying a previous SHA — no ambiguity about what is running in production.

**Why download task definition from AWS instead of storing it in repo?**
Avoids stale task definition files in the repo. The pipeline always works from the live state of AWS — no drift between repo and actual infrastructure.

---

*Built by Sadhvi — Cloud & AI Engineer | Calgary, AB*
*GitHub: github.com/sadvi11*
