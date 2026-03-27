"""
Generators for the Serverless Framework pipeline builder.
Each function returns a string — the content of a generated file.
"""

import re


def _ssm_ref(value: str) -> str:
    if value.startswith("ssm:"):
        return "${" + value + "}"
    return value


# ══════════════════════════════════════════════════════════════════════════════
# serverless.yml
# ══════════════════════════════════════════════════════════════════════════════

def generate_serverless_yml(cfg: dict) -> str:
    slug     = cfg["slug"]
    region   = cfg["aws_region"]
    account  = cfg["aws_account_id"]
    ecr_repo = cfg["ecr_repo_name"]
    stage    = cfg["stage"]
    memory   = cfg["memory"]
    timeout  = cfg["timeout"]
    arch     = cfg["architecture"]
    sel      = cfg["selected"]
    tracing  = "Active" if sel.get("xray") else "PassThrough"
    env_vars = cfg["env_vars"]
    reserved = cfg["reserved_concurrency"]
    warm     = cfg["keep_warm"]

    # ── Environment block ──────────────────────────────────────────────────────
    env_lines = []
    if env_vars:
        env_lines.append("    environment:")
        for ev in env_vars:
            if ev["key"]:
                val = _ssm_ref(ev["value"])
                env_lines.append(f"      {ev['key']}: {val}")
    env_block = "\n".join(env_lines)

    # ── Events block — supports multiple triggers ──────────────────────────────
    event_lines = ["    events:"]
    trigger = cfg["trigger_type"]

    if trigger in ("schedule", "schedule_and_sns") and cfg.get("schedule_expr"):
        event_lines += [
            "      - schedule:",
            f"          rate: {cfg['schedule_expr']}",
            "          enabled: true",
        ]

    if sel.get("sns_trigger") and cfg.get("sns_topic_arn"):
        arn = cfg["sns_topic_arn"]
        topic_name = arn.split(":")[-1]
        event_lines += [
            "      - sns:",
            f"          arn: {arn}",
            f"          topicName: {topic_name}",
        ]

    if sel.get("sqs") and cfg.get("sqs_arn"):
        event_lines += [
            "      - sqs:",
            f"          arn: {cfg['sqs_arn']}",
            f"          batchSize: {cfg['sqs_batch_size']}",
            "          functionResponseType: ReportBatchItemFailures",
        ]

    if sel.get("api_gateway"):
        path   = cfg.get("http_path", "/run").lstrip("/")
        method = cfg.get("http_method", "GET").lower()
        event_lines += [
            "      - httpApi:",
            f"          path: /{path}",
            f"          method: {method}",
        ]

    if len(event_lines) == 1:
        event_block = ""  # no events
    else:
        event_block = "\n".join(event_lines)

    # ── Destinations block ─────────────────────────────────────────────────────
    dest_block = ""
    if sel.get("sns_failure"):
        dest_block = """\
    destinations:
      onFailure:
        type: sns
        arn: !Ref FailureAlertTopic"""

    # ── Concurrency ────────────────────────────────────────────────────────────
    concurrency_lines = []
    if reserved >= 0:
        concurrency_lines.append(f"    reservedConcurrency: {reserved}")
    if warm:
        concurrency_lines.append("    provisionedConcurrency: 1")
    concurrency_block = "\n".join(concurrency_lines)

    # ── IAM statements ────────────────────────────────────────────────────────
    iam_statements = [
        "        - Effect: Allow",
        "          Action: [ssm:GetParameter, ssm:GetParameters, ssm:GetParametersByPath]",
        f"          Resource: arn:aws:ssm:{region}:${{aws:accountId}}:parameter/*",
    ]
    if sel.get("xray"):
        iam_statements += [
            "        - Effect: Allow",
            "          Action: [xray:PutTraceSegments, xray:PutTelemetryRecords]",
            '          Resource: "*"',
        ]
    if sel.get("sns_failure"):
        iam_statements += [
            "        - Effect: Allow",
            "          Action: [sns:Publish]",
            "          Resource: !Ref FailureAlertTopic",
        ]
    if sel.get("s3") and cfg.get("s3_bucket"):
        bucket = cfg["s3_bucket"]
        iam_statements += [
            "        - Effect: Allow",
            "          Action: [s3:GetObject, s3:PutObject, s3:DeleteObject, s3:ListBucket]",
            f"          Resource:",
            f"            - arn:aws:s3:::{bucket}",
            f"            - arn:aws:s3:::{bucket}/*",
        ]
    if sel.get("sqs") and cfg.get("sqs_arn"):
        iam_statements += [
            "        - Effect: Allow",
            "          Action: [sqs:ReceiveMessage, sqs:DeleteMessage, sqs:GetQueueAttributes]",
            f"          Resource: {cfg['sqs_arn']}",
        ]
    iam_block = "\n".join(iam_statements)

    # ── Resources ─────────────────────────────────────────────────────────────
    resources_block = ""
    if sel.get("sns_failure"):
        resources_block = """
resources:
  Resources:
    FailureAlertTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: ${self:service}-${sls:stage}-failure-alerts
        DisplayName: "${self:service} Lambda Failure Alerts"

  Outputs:
    FailureAlertTopicArn:
      Value: !Ref FailureAlertTopic
      Export:
        Name: ${self:service}-${sls:stage}-FailureAlertTopicArn"""

    yml = f"""\
# ─────────────────────────────────────────────────────────────────────────────
# {slug} — Serverless Framework v3
# Generated by Pipeline Builder (Serverless Edition)
# ─────────────────────────────────────────────────────────────────────────────
service: {slug}

frameworkVersion: "^3"

provider:
  name: aws
  region: {region}
  architecture: {arch}
  logRetentionInDays: 30
  tracing:
    lambda: {tracing}

  # ECR image — built and pushed via build.sh / GitHub Actions workflow 1
  ecr:
    images:
      app:
        uri: {account}.dkr.ecr.{region}.amazonaws.com/{ecr_repo}:${{env:IMAGE_TAG, 'latest'}}

  # IAM — Serverless auto-attaches these to the Lambda execution role
  iam:
    role:
      statements:
{iam_block}

  tags:
    Service: {slug}
    Stage: ${{sls:stage}}
    ManagedBy: ServerlessFramework
    GeneratedBy: PipelineBuilder

plugins:
  - serverless-prune-plugin

custom:
  prune:
    automatic: true
    number: 3   # keep last 3 Lambda versions

functions:
  main:
    image:
      name: app
    memorySize: {memory}
    timeout: {timeout}
{env_block}
{event_block}
{dest_block}
{concurrency_block}
{resources_block}
"""
    yml = re.sub(r"\n{3,}", "\n\n", yml)
    return yml.strip() + "\n"


# ══════════════════════════════════════════════════════════════════════════════
# Dockerfile
# ══════════════════════════════════════════════════════════════════════════════

def generate_dockerfile(cfg: dict) -> str:
    runtime = cfg["python_runtime"]
    py_ver  = runtime.replace("python", "")
    return f"""\
# ─────────────────────────────────────────────────────────────────────────────
# {cfg['slug']} Lambda — Docker image  (Python {py_ver})
# ─────────────────────────────────────────────────────────────────────────────
FROM public.ecr.aws/lambda/python:{py_ver}

# System deps (psycopg2 needs libpq)
RUN dnf install -y gcc postgresql-devel python3-devel && dnf clean all

WORKDIR ${{LAMBDA_TASK_ROOT}}

COPY lambda/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler + any helper files in lambda/
COPY lambda/ .

CMD ["handler.handler"]
"""


# ══════════════════════════════════════════════════════════════════════════════
# build.sh
# ══════════════════════════════════════════════════════════════════════════════

def generate_buildsh(cfg: dict) -> str:
    arch     = cfg["architecture"]
    platform = "linux/amd64" if arch == "x86_64" else "linux/arm64"
    return f"""\
#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build.sh — Build Docker image and push to ECR
# Usage: IMAGE_TAG=<git-sha> ./build.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ACCOUNT_ID="{cfg['aws_account_id']}"
REGION="{cfg['aws_region']}"
REPO_NAME="{cfg['ecr_repo_name']}"
IMAGE_TAG="${{IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}}"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

echo "▶  Authenticating with ECR..."
aws ecr get-login-password --region "$REGION" | \\
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "▶  Creating ECR repo if it doesn't exist..."
aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" >/dev/null 2>&1 || \\
  aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION" \\
    --image-scanning-configuration scanOnPush=true >/dev/null

echo "▶  Building image ($IMAGE_TAG) for {platform}..."
docker buildx build \\
  --platform {platform} \\
  --provenance=false \\
  --tag "$ECR_URI:$IMAGE_TAG" \\
  --tag "$ECR_URI:latest" \\
  --push \\
  .

echo "✅  Pushed $ECR_URI:$IMAGE_TAG"
echo ""
echo "   Next: IMAGE_TAG=$IMAGE_TAG sls deploy --stage {cfg['stage']}"
"""


# ══════════════════════════════════════════════════════════════════════════════
# migrations/V001__create_table.sql
# ══════════════════════════════════════════════════════════════════════════════

def generate_migration_sql(cfg: dict) -> str:
    schema  = cfg["db_schema"]
    table   = cfg["db_table"]
    columns = cfg["db_columns"]
    cols_sql, pk_cols = [], []
    for col in columns:
        if not col["name"]: continue
        parts = [f'    "{col["name"]}"', col["type"]]
        if col["pk"]: pk_cols.append(f'"{col["name"]}"')
        if not col["nullable"] and not col["pk"]: parts.append("NOT NULL")
        if col["default"]: parts.append(f"DEFAULT {col['default']}")
        cols_sql.append(" ".join(parts))
    if pk_cols: cols_sql.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
    body = ",\n".join(cols_sql)
    return f"""\
-- V001__create_{table}.sql
CREATE SCHEMA IF NOT EXISTS "{schema}";
CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
{body}
);
CREATE INDEX IF NOT EXISTS idx_{table}_created_at ON "{schema}"."{table}" (created_at DESC);
COMMENT ON TABLE "{schema}"."{table}" IS '{cfg["pipeline_name"]} output';
"""


# ══════════════════════════════════════════════════════════════════════════════
# .github/workflows/1-deploy-ecr.yml
# ══════════════════════════════════════════════════════════════════════════════

def generate_github_deploy_ecr(cfg: dict) -> str:
    region = cfg['aws_region']
    account = cfg['aws_account_id']
    repo = cfg['ecr_repo_name']
    arch = cfg['architecture']
    platform = "linux/amd64" if arch == "x86_64" else "linux/arm64"
    return f"""\
# 1-deploy-ecr.yml — Build Docker image and push to ECR
name: 1 · Deploy ECR Image

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: "Image tag (defaults to git SHA)"
        required: false
        default: ""
  push:
    branches: [main]
    paths: ["lambda/**", "Dockerfile"]

permissions:
  id-token: write
  contents: read

jobs:
  build-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: {region}

      - name: Set image tag
        id: tag
        run: |
          TAG="${{{{ github.event.inputs.image_tag || github.sha }}}}"
          echo "tag=$TAG" >> $GITHUB_OUTPUT

      - name: Log in to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Create ECR repo if it doesn't exist
        run: |
          aws ecr describe-repositories --repository-names {repo} --region {region} >/dev/null 2>&1 || \\
          aws ecr create-repository --repository-name {repo} --region {region} \\
            --image-scanning-configuration scanOnPush=true >/dev/null

      - name: Set ECR resource policy (allow Lambda to pull)
        run: |
          aws ecr set-repository-policy \\
            --repository-name {repo} \\
            --region {region} \\
            --policy-text '{{
              "Version": "2012-10-17",
              "Statement": [{{
                "Sid": "LambdaECRImageAccess",
                "Effect": "Allow",
                "Principal": {{"Service": "lambda.amazonaws.com"}},
                "Action": [
                  "ecr:GetDownloadUrlForLayer",
                  "ecr:BatchGetImage",
                  "ecr:BatchCheckLayerAvailability"
                ]
              }}]
            }}'

      - name: Build and push to ECR
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          platforms: {platform}
          provenance: false
          tags: |
            {account}.dkr.ecr.{region}.amazonaws.com/{repo}:${{{{ steps.tag.outputs.tag }}}}
            {account}.dkr.ecr.{region}.amazonaws.com/{repo}:latest

      - name: Summary
        run: |
          echo "### ✅ ECR image pushed" >> $GITHUB_STEP_SUMMARY
          echo "Tag: ${{{{ steps.tag.outputs.tag }}}}" >> $GITHUB_STEP_SUMMARY
          echo "Use this tag when running workflow 2b to deploy prod." >> $GITHUB_STEP_SUMMARY
"""


# ══════════════════════════════════════════════════════════════════════════════
# .github/workflows/2a-deploy-staging.yml  (auto on push to main)
# ══════════════════════════════════════════════════════════════════════════════

def generate_github_deploy_lambda(cfg: dict) -> str:
    """Returns the staging workflow (2a). Kept as generate_github_deploy_lambda for back-compat."""
    return generate_github_deploy_staging(cfg)


def generate_github_deploy_staging(cfg: dict) -> str:
    region = cfg['aws_region']
    return f"""\
# 2a-deploy-staging.yml
# Triggers automatically on every push to main.
# Deploys to staging and smoke tests. If this passes, run 2b manually to go to prod.
name: 2a · Deploy → staging (auto)

on:
  push:
    branches: [main]
    paths: ["lambda/**", "Dockerfile", "serverless.yml"]
  workflow_dispatch:
    inputs:
      image_tag:
        description: "ECR image tag (defaults to git SHA)"
        required: false
        default: ""

permissions:
  id-token: write
  contents: read

jobs:
  deploy-staging:
    name: Deploy → staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: {region}

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Serverless Framework + plugins
        run: |
          npm install -g serverless@^3
          sls plugin install -n serverless-prune-plugin

      - name: Set image tag
        id: tag
        run: |
          TAG="${{{{ github.event.inputs.image_tag || github.sha }}}}"
          echo "tag=$TAG" >> $GITHUB_OUTPUT

      - name: sls deploy → staging
        run: sls deploy --stage staging --region {region} --verbose
        env:
          IMAGE_TAG: ${{{{ steps.tag.outputs.tag }}}}

      - name: Smoke test staging
        run: sls invoke --function main --stage staging --region {region} --log

      - name: Summary
        run: |
          echo "### ✅ Staging deploy succeeded" >> $GITHUB_STEP_SUMMARY
          echo "Image tag: ${{{{ steps.tag.outputs.tag }}}}" >> $GITHUB_STEP_SUMMARY
          echo "When ready for prod → run workflow **2b · Deploy → prod** with this image tag." >> $GITHUB_STEP_SUMMARY
"""


# ══════════════════════════════════════════════════════════════════════════════
# .github/workflows/2b-deploy-prod.yml  (manual trigger only)
# ══════════════════════════════════════════════════════════════════════════════

def generate_github_deploy_prod(cfg: dict) -> str:
    region = cfg['aws_region']
    prod_stage = cfg['stage']
    return f"""\
# 2b-deploy-prod.yml
# Manual trigger only — run this after staging looks good.
# Go to Actions → "2b · Deploy → prod" → Run workflow → paste the git SHA from the staging run.
name: 2b · Deploy → {prod_stage} (manual)

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: "ECR image tag to deploy (copy the git SHA from the 2a staging run)"
        required: true

permissions:
  id-token: write
  contents: read

jobs:
  deploy-prod:
    name: Deploy → {prod_stage}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: {region}

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Serverless Framework + plugins
        run: |
          npm install -g serverless@^3
          sls plugin install -n serverless-prune-plugin

      - name: sls deploy → {prod_stage}
        run: sls deploy --stage {prod_stage} --region {region} --verbose
        env:
          IMAGE_TAG: ${{{{ github.event.inputs.image_tag }}}}

      - name: Smoke test prod
        run: sls invoke --function main --stage {prod_stage} --region {region} --log

      - name: Summary
        run: |
          echo "### 🚀 Prod deploy succeeded" >> $GITHUB_STEP_SUMMARY
          echo "Stage: {prod_stage} · Image: ${{{{ github.event.inputs.image_tag }}}}" >> $GITHUB_STEP_SUMMARY
"""


# ══════════════════════════════════════════════════════════════════════════════
# .github/workflows/3-apply-migration.yml
# ══════════════════════════════════════════════════════════════════════════════

def generate_github_apply_migration(cfg: dict) -> str:
    table  = cfg["db_table"]
    region = cfg["aws_region"]
    stage  = cfg["stage"]
    slug   = cfg["slug"]
    schema = cfg["db_schema"]
    return f"""\
# 3-apply-migration.yml — Run psql migration against Postgres
#
# One-time secret setup in AWS Secrets Manager:
#   Name: {slug}/staging/creds   (and {slug}/{stage}/creds for prod)
#   Type: Other → Key/value pairs
#   Keys: db-host, db-port, db-name, db-user, db-password
#
name: 3 · Apply Migration

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        type: choice
        options: [staging, {stage}]
        default: staging
      confirm_table:
        description: "Type the target table name to confirm: {table}"
        required: true

permissions:
  id-token: write
  contents: read

jobs:
  migrate:
    runs-on: ubuntu-latest
    if: github.event.inputs.confirm_table == '{table}'
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: {region}

      - name: Fetch DB credentials from Secrets Manager
        id: db
        run: |
          ENV="${{{{ github.event.inputs.environment }}}}"
          SECRET=$(aws secretsmanager get-secret-value \\
            --secret-id "{slug}/$ENV/creds" \\
            --query SecretString \\
            --output text \\
            --region {region})
          DB_HOST=$(echo "$SECRET" | jq -r '.db_host')
          DB_PORT=$(echo "$SECRET" | jq -r '.db_port')
          DB_NAME=$(echo "$SECRET" | jq -r '.db_name')
          DB_USER=$(echo "$SECRET" | jq -r '.db_user')
          DB_PASS=$(echo "$SECRET" | jq -r '.db_password')
          echo "::add-mask::$DB_PASS"
          printf '%s' "$DB_PASS" > /tmp/pgpass
          chmod 600 /tmp/pgpass
          echo "host=$DB_HOST" >> $GITHUB_OUTPUT
          echo "port=$DB_PORT" >> $GITHUB_OUTPUT
          echo "name=$DB_NAME" >> $GITHUB_OUTPUT
          echo "user=$DB_USER" >> $GITHUB_OUTPUT

      - name: Apply migration
        env:
          PGHOST: ${{{{ steps.db.outputs.host }}}}
          PGPORT: ${{{{ steps.db.outputs.port }}}}
          PGDATABASE: ${{{{ steps.db.outputs.name }}}}
          PGUSER: ${{{{ steps.db.outputs.user }}}}
          PGSSLMODE: require
        run: |
          export PGPASSWORD=$(cat /tmp/pgpass)
          psql -f migrations/V001__create_{table}.sql -v ON_ERROR_STOP=1

      - name: Verify table exists
        env:
          PGHOST: ${{{{ steps.db.outputs.host }}}}
          PGPORT: ${{{{ steps.db.outputs.port }}}}
          PGDATABASE: ${{{{ steps.db.outputs.name }}}}
          PGUSER: ${{{{ steps.db.outputs.user }}}}
          PGSSLMODE: require
        run: |
          export PGPASSWORD=$(cat /tmp/pgpass)
          psql -c "\\d {schema}.{table}"
"""


# ══════════════════════════════════════════════════════════════════════════════
# OIDC IAM Role CloudFormation template
# ══════════════════════════════════════════════════════════════════════════════

def generate_github_oidc_role_cfn() -> str:
    return """\
# oidc-role.yaml — One-time setup: IAM Role for GitHub Actions OIDC
# Deploy with:
#   aws cloudformation deploy \\
#     --template-file oidc-role.yaml \\
#     --stack-name github-actions-role \\
#     --capabilities CAPABILITY_IAM \\
#     --parameter-overrides GitHubOrg=YOUR_ORG GitHubRepo=YOUR_REPO
AWSTemplateFormatVersion: "2010-09-09"
Description: IAM Role for GitHub Actions OIDC (no static keys)

Parameters:
  GitHubOrg:
    Type: String
    Description: Your GitHub organisation or username
  GitHubRepo:
    Type: String
    Description: Repository name (e.g. arbitrum-block-fetcher)

Resources:

  GitHubOIDCProvider:
    Type: AWS::IAM::OIDCProvider
    Properties:
      Url: https://token.actions.githubusercontent.com
      ClientIdList: [sts.amazonaws.com]
      ThumbprintList: [6938fd4d98bab03faadb97b34396831e3780aea1]

  GitHubActionsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: GitHubActionsDeployRole
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref GitHubOIDCProvider
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
              StringLike:
                # Only tokens from YOUR repo can assume this role
                token.actions.githubusercontent.com:sub:
                  !Sub repo:${GitHubOrg}/${GitHubRepo}:*
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
      Policies:
        - PolicyName: ServerlessDeployPolicy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              # Serverless Framework needs these to deploy
              - Effect: Allow
                Action:
                  - lambda:*
                  - events:*
                  - sns:*
                  - sqs:GetQueueAttributes
                  - iam:GetRole
                  - iam:CreateRole
                  - iam:DeleteRole
                  - iam:AttachRolePolicy
                  - iam:DetachRolePolicy
                  - iam:PutRolePolicy
                  - iam:DeleteRolePolicy
                  - iam:PassRole
                  - cloudformation:*
                  - s3:*
                  - logs:*
                  - ssm:GetParameter
                  - ssm:GetParameters
                  - ssm:GetParametersByPath
                  - secretsmanager:GetSecretValue
                Resource: "*"

Outputs:
  RoleArn:
    Description: Paste this into GitHub Secret AWS_DEPLOY_ROLE_ARN
    Value: !GetAtt GitHubActionsRole.Arn
    Export:
      Name: GitHubActionsDeployRoleArn
"""


# ══════════════════════════════════════════════════════════════════════════════
# README.md
# ══════════════════════════════════════════════════════════════════════════════

def generate_readme(cfg: dict) -> str:
    sel   = cfg["selected"]
    slug  = cfg["slug"]
    stage = cfg["stage"]

    trigger_desc = "None configured"
    if sel.get("eventbridge"): trigger_desc = f"EventBridge — `{cfg.get('schedule_expr','')}`"
    elif sel.get("sns_trigger"): trigger_desc = f"SNS — `{cfg.get('sns_topic_arn','')}`"
    elif sel.get("sqs"): trigger_desc = f"SQS — `{cfg.get('sqs_arn','')}`"
    elif sel.get("api_gateway"): trigger_desc = f"HTTP API — `{cfg.get('http_method','')} {cfg.get('http_path','')}`"

    components = [c for c in ["Lambda","EventBridge","SNS Trigger","SQS","API Gateway","Failure Alerts","Postgres/RDS","S3","X-Ray"]
                  if sel.get({"Lambda":"lambda","EventBridge":"eventbridge","SNS Trigger":"sns_trigger",
                               "SQS":"sqs","API Gateway":"api_gateway","Failure Alerts":"sns_failure",
                               "Postgres/RDS":"rds","S3":"s3","X-Ray":"xray"}.get(c,""))]

    return f"""\
# {slug}

> Generated by **Pipeline Builder · Serverless Framework Edition**

## Components
{chr(10).join(f"- {c}" for c in components)}

## Config

| | |
|---|---|
| Framework | Serverless Framework v3 |
| Trigger | {trigger_desc} |
| Memory | {cfg['memory']} MB · Timeout {cfg['timeout']}s |
| Architecture | {cfg['architecture']} |
| Region / Stage | {cfg['aws_region']} / {stage} |

## First deploy

```bash
# 1. Build + push Docker image
IMAGE_TAG=$(git rev-parse --short HEAD) ./build.sh

# 2. Deploy with Serverless
IMAGE_TAG=<tag> sls deploy --stage {stage} --region {cfg['aws_region']} --verbose

# 3. Apply DB migration (if Postgres selected)
psql $DATABASE_URL -f migrations/V001__create_{cfg.get('db_table','table')}.sql
```

Or run the 3 GitHub Actions workflows in order: **1 → 2 → 3**.

## Useful commands

```bash
sls info --stage {stage}                          # show deployed resources
sls invoke --function main --stage {stage} --log  # test invoke
sls logs --function main --stage {stage} --tail   # live logs
sls deploy --stage {stage} --noDeploy             # dry run
sls remove --stage {stage}                        # destroy stack
```

## Required GitHub Secret

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | ARN of the OIDC IAM role (see CI/CD setup tab) |
"""