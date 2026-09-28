"""Command-line entry point: `python -m tracker <command>`."""

from __future__ import annotations

import argparse
import json
import sys

from tracker import __version__
from tracker.config import load_config
from tracker.log import get_logger, setup_logging

log = get_logger("tracker.cli")


def cmd_version(args, cfg) -> int:
    print(f"news-tracker {__version__} — profile: {cfg.settings.profile.name}")
    return 0


def cmd_config(args, cfg) -> int:
    """Print the resolved settings (secrets are shown only as present/missing)."""
    out = cfg.settings.model_dump()
    out["_config_dir"] = str(cfg.config_dir)
    out["_secrets"] = {k: bool(v) for k, v in cfg.secrets.model_dump().items()}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracker", description="News & Election Tracker")
    parser.add_argument("--config", help="profile directory (default: ./config or $TRACKER_CONFIG_DIR)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="show version and active profile").set_defaults(func=cmd_version)
    sub.add_parser("config", help="print resolved settings").set_defaults(func=cmd_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page; headlines are in Hindi, Tamil, etc.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    cfg = load_config(args.config)
    return args.func(args, cfg)
