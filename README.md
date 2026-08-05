# Terraform-AI-Drift-Detector

A cloud-agnostic Terraform drift detection platform that compares Terraform state files with actual cloud resource metadata without running `terraform plan` or `terraform apply`.

## What it does

- Reads expected resources from local Terraform state files.
- Fetches actual AWS resources directly from your AWS account when `--actual` is not supplied.
- Normalizes expected and actual resources into a shared model.
- Detects missing resources, unexpected resources, attribute changes, and tag drift.
- Emits console or JSON reports for CLI, automation, and future dashboard usage.
- Keeps provider fetching behind an extensible adapter interface.

## Quickstart with your AWS account

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[aws,dev]'
aws sts get-caller-identity

drift-detector scan \
  --state /path/to/terraform.tfstate \
  --provider aws \
  --profile your-aws-profile \
  --region us-east-1
```

If you omit `--actual`, the CLI performs a live AWS scan and compares AWS API results with the Terraform state file.

## Fixture-based local test mode

You can still test without AWS credentials by providing normalized actual-resource JSON:

```bash
drift-detector state inspect tests/fixtures/terraform.tfstate
drift-detector scan --state tests/fixtures/terraform.tfstate --actual examples/actual-resources.json
```

## CLI examples

Inspect managed resources in Terraform state:

```bash
drift-detector state inspect ./terraform.tfstate
```

Run a live AWS scan and print a console report:

```bash
drift-detector scan --state ./terraform.tfstate --provider aws --profile default --region us-east-1
```

Run a live AWS scan and write JSON output:

```bash
drift-detector scan --config examples/config.yaml --output json --file report.json
```

Run a fixture-based scan with manually supplied actual resources:

```bash
drift-detector scan --state ./terraform.tfstate --actual ./actual-resources.json
```

## Configuration

```yaml
provider:
  name: aws
  profile: default
  regions:
    - us-east-1
state:
  source: local
  path: ./terraform.tfstate
ignore:
  attributes:
    - "*.arn"
    - "*.last_modified"
  tags:
    - "aws:*"
```

## Supported live AWS resources

The live AWS provider currently fetches these Terraform resource types when they appear in state:

- `aws_instance`
- `aws_security_group`
- `aws_s3_bucket`
- `aws_iam_role`
- `aws_lambda_function`

## Current implementation status

This MVP includes the project scaffold, typed models, local state reader, resource extractor, live AWS provider fetcher, drift engine, console reporter, JSON reporter, CLI commands, examples, and unit tests.

## Architecture

```text
Terraform State -> State Reader -> Expected Resource Model
AWS APIs/Input -> Cloud Fetcher -> Actual Resource Model
Expected + Actual -> Drift Engine -> Console/JSON Report
```

## Troubleshooting

### S3 buckets without tags

AWS returns a `NoSuchTagSet` ClientError when an S3 bucket exists but has no tags. The scanner treats that as an empty tag set so untagged buckets can still be compared instead of failing the scan.

## Console output format

The default console report is intentionally compact: it prints scan metadata, a summary block, and one tabular row per finding with kind, severity, resource, field, expected value, and actual value.
