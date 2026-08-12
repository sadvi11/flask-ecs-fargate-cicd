# Flask ECS Fargate CI/CD

[![CI](https://github.com/sadvi11/flask-ecs-fargate-cicd/actions/workflows/ci.yml/badge.svg)](https://github.com/sadvi11/flask-ecs-fargate-cicd/actions/workflows/ci.yml)
![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate%20·%20ECR-FF9900?logo=amazonaws&logoColor=white)
![Region](https://img.shields.io/badge/Region-ca--central--1-232F3E)
![Auth](https://img.shields.io/badge/AWS%20auth-OIDC%20·%20no%20stored%20keys-3ecca0)
![Tags](https://img.shields.io/badge/Images-SHA--tagged-2088ff)
![License](https://img.shields.io/badge/License-MIT-green)

> A containerized Python API on AWS ECS Fargate, built and tested by GitHub Actions on
> every commit and released to ECR and ECS through a pipeline that stores no AWS
> credentials.

**Live demo:** [flask-ecs-fargate-cicd.onrender.com/health](https://flask-ecs-fargate-cicd.onrender.com/health)
· *(free tier — the first request after an idle period cold-starts and can take ~15s)*

---

## What runs automatically, and what does not

Being precise about this, because "fully automated" is easy to claim and easy to check.

| Workflow | Trigger | What it does |
|---|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | **Every push and PR** | Installs, runs tests, builds the image. Fails the commit if any step fails. |
| [`deploy.yml`](.github/workflows/deploy.yml) | **Manual** (`workflow_dispatch`) | Builds, pushes to ECR, renders a new task definition and rolls out to ECS. |

Deployment is deliberately manual rather than on every push. It targets a live ECS
cluster, and a public repository whose CI requires a funded AWS account to stay green
is a repository that goes red the moment the account is torn down. CI proves the code;
deploy is invoked when a deploy is actually wanted.

---

## What this project demonstrates

- Containerizing a Python Flask API with Docker (multi-platform `linux/amd64` build)
- Storing container images in Amazon ECR with versioned tags per commit SHA
- Running containers serverlessly on AWS ECS Fargate — no EC2 instances to manage
- Rolling deployment to ECS with `wait-for-service-stability`, so the pipeline fails
  rather than reporting success while the new task definition never stabilises
- CloudWatch logging for production observability
- **No AWS credential is stored anywhere.** Authentication is OIDC federation — GitHub
  presents a signed token, AWS validates it against a trust policy scoped to this
  repository, and returns credentials that expire

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

**There is no AWS access key in this repository or in its settings.** The pipeline
authenticates by OIDC workload identity federation: GitHub mints a short-lived signed
token, AWS validates it against a trust policy that names this specific repository,
and returns temporary credentials. Nothing persists between runs.

That removes three failure modes at once. There is no key to leak. There is no
rotation task to forget. And a fork or a pull request from an outside contributor
cannot obtain credentials, because the trust policy is scoped to this repository —
which a stored secret in an unprotected workflow would not have prevented.

- **OIDC federation, no long-lived credentials** — the only configured value is the
  role ARN, which is not a secret and is useless without the matching trust policy
- Account ID is never committed — it is resolved at runtime from the ECR login output
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

**4. Create the OIDC trust so GitHub can authenticate without a key.**

Register GitHub as an identity provider in IAM (once per AWS account):

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com
```

Then create a role whose trust policy names **this repository**. The `sub` condition is
the important line — without it, any repository on GitHub could assume the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
      "StringLike":   { "token.actions.githubusercontent.com:sub": "repo:sadvi11/flask-ecs-fargate-cicd:*" }
    }
  }]
}
```

Attach permissions for ECR push and ECS deploy, scoped to the resources above rather
than `*`.

**5. Add one repository variable:** `AWS_DEPLOY_ROLE_ARN`, set to that role's ARN.

That is the entire configuration. No access key, no secret key, no account ID.

**6. Run the deploy workflow manually** from the Actions tab. If `AWS_DEPLOY_ROLE_ARN`
is not set, the workflow reports that clearly and stops instead of failing partway
through with a credentials error.

> **Note on the `sub` claim.** The trust policy above uses the documented
> `repo:owner/name:*` format. GitHub does not always present that exact string — in a
> sibling project it presented a subject containing immutable numeric account and
> repository IDs, and the role would not assume until the trust policy matched what was
> actually sent. If federation fails with `AADSTS`-style "no matching identity", read
> the real `sub` claim out of the failed run rather than trusting the documented shape.

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
