# WHY.md — Why This Project Exists

## The gap it closes

Every cloud engineering job description in Canada mentions ECS Fargate and CI/CD pipelines. Before this project, my portfolio had Docker, Kubernetes (EKS), and EC2 deployments — but not Fargate specifically.

Hiring managers scan for exact keywords. "ECS Fargate" was missing. This project closes that gap permanently.

---

## Why ECS Fargate specifically — not EKS or EC2

**ECS Fargate** is the dominant choice for teams that want container orchestration without managing servers. You define CPU and memory at the task level, AWS handles everything underneath — no patching, no capacity planning, no node groups.

**EKS** gives you full Kubernetes control but adds operational overhead. Teams choose EKS when they need advanced scheduling, custom operators, or multi-cluster federation.

**EC2** gives you the most control but the most responsibility. You manage the OS, patching, and capacity.

For a 3–10 person engineering team running containerized APIs, Fargate is the right default. That is why it appears in most JDs — and why I built this project on Fargate specifically.

---

## Why GitHub Actions — not AWS CodePipeline

AWS CodePipeline is powerful but adds cost and complexity for straightforward deployments. GitHub Actions is:

- Free for public repos
- Colocated with the code — no context switching
- Uses the same AWS open-source actions that AWS themselves recommend
- Industry standard: most engineering teams use GitHub Actions today

AWS's own blog uses GitHub Actions for ECS Fargate CI/CD tutorials. That is the validation I needed.

---

## What I learned building this

**The platform mismatch problem:** My Mac uses ARM64 (Apple Silicon). ECS Fargate requires AMD64. Docker build without `--platform linux/amd64` produces an image that fails silently on Fargate. The fix is one flag — but the lesson is: always match your build platform to your runtime platform.

**Health checks are not optional:** The first deployment failed because the slim Python base image had no `curl`. The ECS health check ran `curl /health` and got `command not found`. Task failed, ECS rolled back. Fix: add `RUN apt-get install -y curl` to Dockerfile. Now health checks pass.

**Credentials in repos are a liability:** The first version of the task definition had my real AWS account ID hardcoded. Fixed by: storing account ID as a GitHub Secret, using `ACCOUNT_ID` as a placeholder in the file, and injecting the real value via `sed` in the pipeline. No sensitive value ever touches the repo.

**Stateless task definitions:** Instead of storing the task definition in the repo and keeping it in sync manually, the pipeline fetches the current task definition live from AWS with `aws ecs describe-task-definition`. This eliminates config drift — the pipeline always works from the actual state of AWS.

---

## How this maps to real engineering work

At Nokia, I managed CNF (Containerized Network Function) deployments using CBAM — Nokia's container lifecycle manager. CBAM handled rolling upgrades, health checks, and scaling. When I moved to AWS, ECS Fargate was immediately familiar:

- CBAM Helm chart → ECS task definition
- CBAM rolling upgrade → ECS rolling deployment (`minimum_healthy_percent: 100`)
- CBAM liveness probe → ECS health check
- CBAM HPA → ECS Application Auto Scaling

This project is not just a tutorial follow-through. It is a translation of carrier-scale container operations into AWS-native tooling.

---

## What a production version would add

This project is a portfolio demonstration. A production version would include:

- **ALB** instead of direct task IP — stable DNS, SSL termination, health-check-based routing
- **Private subnets** for ECS tasks — tasks should not have public IPs
- **ECR image scanning** — `scanOnPush: true` to catch vulnerabilities on every push
- **ECS Service Auto Scaling** — scale tasks based on CPU or request count
- **GitHub Environments** — require manual approval before deploying to production
- **Secrets Manager** — inject runtime secrets into containers without environment variables

---

*Built by Sadhvi — Cloud & AI Engineer | Calgary, AB*
*GitHub: github.com/sadvi11*
