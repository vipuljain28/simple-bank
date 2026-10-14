# Development ECS Deployment

This setup deploys only the API to an ECS Fargate dev service in `eu-north-1`.
It uses the existing `itc/fastapi-demo-vipul` ECR repository and GitHub Actions
OIDC; it does not store AWS access keys in GitHub.

## Important limitations

- This is a development deployment, not a production architecture.
- The service uses one Fargate task and in-memory SQLite. Customer and account
  data is lost whenever the task restarts or is replaced; do not use real
  customer or transaction data.
- The public endpoint uses the AWS-provided CloudFront HTTPS hostname, so it can
  be opened from any laptop without registering a domain. The load balancer is
  restricted to CloudFront origin traffic and a WAF origin-verification header
  prevents bypassing HTTPS through its AWS hostname.
- Contact delivery and transfer verification are intentionally unconfigured
  and fail closed. This deployment does not enable real transfers.
- CloudFront, WAF, Fargate, the application load balancer, Secrets Manager, and
  CloudWatch Logs can incur ongoing charges.

## Bootstrap the dev service

The stack creates the service with zero running tasks so it can be created
before the first image is pushed. The first GitHub Actions deployment builds
and pushes the API image, then starts one task. Run these commands from the
repository root in PowerShell with the AWS CLI configured.

```powershell
$Region = "eu-north-1"
$Repository = "itc/fastapi-demo-vipul"
$AccountId = aws sts get-caller-identity --profile itc --query Account --output text
$Registry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$ImageUri = "${Registry}/${Repository}:bootstrap"

aws cloudformation deploy `
  --profile itc `
  --region $Region `
  --stack-name simple-bank-dev `
  --template-file infra/ecs-dev.yml `
  --capabilities CAPABILITY_NAMED_IAM `
  --parameter-overrides `
    "ImageUri=$ImageUri"
```

The stack creates a dev VPC, an internet-facing HTTPS CloudFront endpoint, an
origin-restricted HTTP load balancer, an origin-verification WAF rule, an ECS
Fargate cluster/service, log retention, generated Secrets Manager values, and
a branch-scoped GitHub Actions role. The AWS account must already have the
GitHub Actions OIDC provider for `token.actions.githubusercontent.com`.

After the stack is created, copy its outputs from the CloudFormation console or
run:

```powershell
aws cloudformation describe-stacks `
  --profile itc `
  --region eu-north-1 `
  --stack-name simple-bank-dev `
  --query "Stacks[0].Outputs" `
  --output table
```

In the GitHub repository settings, add these **Actions variables** using the
stack outputs where applicable:

| Variable | Value |
| --- | --- |
| `AWS_REGION` | `eu-north-1` |
| `AWS_ROLE_ARN` | `GitHubDeployRoleArn` |
| `ECR_REPOSITORY` | `itc/fastapi-demo-vipul` |
| `ECS_CLUSTER` | `EcsClusterName` |
| `ECS_SERVICE` | `EcsServiceName` |
| `ECS_TASK_FAMILY` | `EcsTaskFamily` |
| `ECS_CONTAINER_NAME` | `EcsContainerName` |

The workflow at `.github/workflows/deploy-api-dev.yml` runs API unit/route
tests, builds and pushes an image tagged with the commit SHA, registers a task
definition revision, then waits for the dev service to stabilize. It deploys
on pushes to `main` that change `apps/api/**`, or via manual workflow dispatch
from `main`.
