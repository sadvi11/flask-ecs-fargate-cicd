# Architecture: Flask ECS Fargate CI/CD Pipeline

GitHub renders this Mermaid diagram natively. It shows two views:
1. **CI/CD pipeline flow** — what happens on every git push
2. **AWS runtime architecture** — how traffic flows to the running app

---

## CI/CD Pipeline — triggered on every push to main

```mermaid
flowchart LR
  Dev(["Developer\npushes code"])

  subgraph GitHub ["GitHub"]
    Repo["Repository\n(main branch)"]
    subgraph Actions ["GitHub Actions Runner"]
      Step1["1. Checkout code"]
      Step2["2. Configure\nAWS credentials\n(GitHub Secrets)"]
      Step3["3. Login to\nAmazon ECR"]
      Step4["4. Build Docker image\nlinux/amd64\ntag: git commit SHA"]
      Step5["5. Push image\nto ECR"]
      Step6["6. Fetch task def\nfrom AWS"]
      Step7["7. Inject new\nimage URI"]
      Step8["8. Deploy to ECS\nwait for stability"]
    end
  end

  subgraph AWS ["AWS — ca-central-1"]
    ECR["Amazon ECR\nPrivate Registry\nimmutable tags"]
    ECS["ECS Fargate Service\nflask-ecs-cluster\n1 task / 256 CPU / 512MB"]
    CW["CloudWatch Logs\n/ecs/flask-ecs-fargate"]
    IAM["IAM\necsTaskExecutionRole\nleast privilege"]
  end

  Dev --> Repo
  Repo --> Step1
  Step1 --> Step2
  Step2 --> Step3
  Step3 --> Step4
  Step4 --> Step5
  Step5 --> Step6
  Step6 --> Step7
  Step7 --> Step8
  Step5 -->|"push image"| ECR
  Step8 -->|"update service"| ECS
  ECS -->|"pull image"| ECR
  ECS -->|"write logs"| CW
  IAM -->|"grants ECR pull\n+ CloudWatch write"| ECS
```

---

## AWS Runtime Architecture — how traffic reaches the app

```mermaid
flowchart TB
  User(["User / Recruiter\nbrowser or curl"])

  subgraph Internet ["Public Internet"]
    URL["https://flask-ecs-fargate-cicd\n.onrender.com\n\nDemo URL (Render)"]
    AWSIP["http://ECS-PUBLIC-IP:8080\n\nDirect ECS task IP\n(changes on restart)"]
  end

  subgraph VPC ["AWS VPC — Default (ca-central-1)"]
    subgraph PublicSubnet ["Public Subnet"]
      ENI["Elastic Network Interface\npublic IP assigned\nassignPublicIp: ENABLED"]
    end

    subgraph ECSFargate ["ECS Fargate Task"]
      Container["Flask Container\ngunicorn 2 workers\nport 8080"]
      Health["Health Check\nGET /health\nevery 30s"]
    end

    SG["Security Group\ninbound: TCP 8080\noutbound: all"]
  end

  subgraph Monitoring ["Observability"]
    CW["CloudWatch Logs\n/ecs/flask-ecs-fargate\nretention: 30 days"]
  end

  subgraph Security ["Security"]
    IAM["IAM Execution Role\necsTaskExecutionRole\nECR pull + CW write only"]
    Secrets["GitHub Secrets\nAWS_ACCESS_KEY_ID\nAWS_SECRET_ACCESS_KEY\nAWS_ACCOUNT_ID"]
  end

  User --> URL
  User --> AWSIP
  URL -->|"proxied"| Container
  AWSIP --> ENI
  ENI --> SG
  SG --> Container
  Container --> Health
  Container -->|"stdout logs"| CW
  IAM -->|"authorizes"| Container
  Secrets -->|"injected at\npipeline runtime"| IAM
```

---

## Pipeline execution times (real measured values)

| Step | Time |
|---|---|
| Checkout + configure credentials | ~10s |
| ECR login | ~5s |
| Docker build (linux/amd64, cached layers) | ~45s |
| Push to ECR | ~20s |
| Fetch + render task definition | ~5s |
| ECS deploy + stabilization wait | ~60s |
| **Total pipeline duration** | **~2.5 minutes** |

---

## Security design decisions

| Decision | Reason |
|---|---|
| AWS credentials in GitHub Secrets | Never stored in code or config files |
| Account ID injected via `sed` at runtime | No account ID committed to repo |
| Task definition fetched live from AWS | No stale config in repo, no drift |
| IAM role: least privilege | Only ECR pull + CloudWatch write — nothing else |
| `linux/amd64` build platform | ECS Fargate requires AMD64 — not ARM64 (Apple Silicon) |
| Commit SHA as image tag | Every deployment traceable to exact commit — rollback = redeploy SHA |

---

*Architecture sourced from:*
- *[AWS Blog: CI/CD pipeline for Amazon ECS with GitHub Actions](https://aws.amazon.com/blogs/containers/create-a-ci-cd-pipeline-for-amazon-ecs-with-github-actions-and-aws-codebuild-tests/)*
- *[AWS Blog: Automated deployments with GitHub Actions for Amazon ECS](https://aws.amazon.com/blogs/containers/automated-deployments-with-github-actions-for-amazon-ecs-express-mode/)*
- *AWS ECS Fargate official documentation*
