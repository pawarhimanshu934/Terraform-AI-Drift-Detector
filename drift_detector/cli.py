from __future__ import annotations

import argparse
from pathlib import Path

from drift_detector.config import IgnoreConfig, load_config
from drift_detector.engine.comparator import DriftEngine
from drift_detector.reports.console import render_console
from drift_detector.providers.aws import AWSProvider
from drift_detector.reports.json_report import load_actual_resources, render_json, write_json
from drift_detector.state.extractor import extract_expected_resources
from drift_detector.state.reader import TerraformStateReader


def _inspect_state(args: argparse.Namespace) -> None:
    resources = extract_expected_resources(TerraformStateReader().read(args.path))
    print(f"Managed resources: {len(resources)}")
    for resource in resources:
        print(f"- {resource.identity} ({resource.address})")


def _scan(args: argparse.Namespace) -> None:
    ignore = IgnoreConfig()
    state_path = args.state
    provider = args.provider
    profile = args.profile
    regions = args.region
    if args.config:
        loaded = load_config(args.config)
        ignore = loaded.ignore
        provider = loaded.provider.name
        state_path = Path(loaded.state.path)
        profile = profile or loaded.provider.profile
        regions = regions or loaded.provider.regions
    if state_path is None:
        raise SystemExit("Provide --state or --config.")

    expected = extract_expected_resources(TerraformStateReader().read(state_path))
    actual_resources = load_actual_resources(args.actual) if args.actual else _fetch_live_resources(provider, expected, profile, regions)
    report = DriftEngine(ignore).compare(expected, actual_resources, provider=provider, state_source=str(state_path))
    if args.file:
        write_json(report, args.file)
    print(render_json(report) if args.output == "json" else render_console(report), end="")


def _fetch_live_resources(provider: str, expected, profile: str | None, regions: list[str]):
    if provider != "aws":
        raise SystemExit(f"Live scans for provider {provider!r} are not implemented yet. Provide --actual JSON instead.")
    return AWSProvider(profile=profile, regions=regions).fetch_resources(expected)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terraform state drift detection without terraform plan/apply.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    state_parser = subparsers.add_parser("state")
    state_subparsers = state_parser.add_subparsers(dest="state_command", required=True)
    inspect_parser = state_subparsers.add_parser("inspect")
    inspect_parser.add_argument("path", type=Path)
    inspect_parser.set_defaults(func=_inspect_state)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--state", type=Path)
    scan_parser.add_argument("--actual", type=Path)
    scan_parser.add_argument("--config", type=Path)
    scan_parser.add_argument("--provider", default="aws")
    scan_parser.add_argument("--profile", help="AWS profile name for live AWS scans.")
    scan_parser.add_argument("--region", action="append", default=[], help="AWS region to scan; repeat for multiple regions.")
    scan_parser.add_argument("--output", choices=["console", "json"], default="console")
    scan_parser.add_argument("--file", type=Path)
    scan_parser.set_defaults(func=_scan)
    return parser


def app() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    app()
