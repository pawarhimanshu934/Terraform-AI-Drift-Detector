# Terraform-AI-Drift-Detector

A cloud-agnostic Terraform drift detection platform that compares Terraform state files with actual cloud resource metadata without running `terraform plan` or `terraform apply`.

## What it does

- Reads expected resources from local Terraform state files.
- Normalizes expected and actual resources into a shared model.
- Detects missing resources, unexpected resources, attribute changes, and tag drift.
- Emits console or JSON reports for CLI, automation, and future dashboard usage.
- Keeps provider fetching behind an extensible adapter interface.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
drift-detector state inspect tests/fixtures/terraform.tfstate
drift-detector scan --state tests/fixtures/terraform.tfstate --actual examples/actual-resources.json
```

## CLI examples

Inspect managed resources in Terraform state:

```bash
drift-detector state inspect ./terraform.tfstate
```

Run a scan and print a console report:

```bash
drift-detector scan --state ./terraform.tfstate --actual ./actual-resources.json
```

Run a scan and write JSON output:

```bash
drift-detector scan --config examples/config.yaml --actual examples/actual-resources.json --output json --file report.json
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

## Current implementation status

This initial MVP includes the project scaffold, typed models, local state reader, resource extractor, drift engine, console reporter, JSON reporter, CLI commands, examples, and unit tests. The AWS provider is intentionally exposed as an adapter skeleton so live API fetchers can be added without changing the drift engine.

## Architecture

```text
Terraform State -> State Reader -> Expected Resource Model
Cloud APIs/Input -> Cloud Fetcher -> Actual Resource Model
Expected + Actual -> Drift Engine -> Console/JSON Report
```
