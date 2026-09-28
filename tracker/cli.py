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


def cmd_sources(args, cfg) -> int:
    from tracker.sources import check_sources, export_engine_feeds, load_sources

    specs = load_sources(cfg.config_dir, include_disabled=getattr(args, "all", False))
    if args.action == "list":
        for s in specs:
            flag = "" if s.enabled else "  (disabled)"
            print(f"{s.id:32} {s.type:15} {s.language:3} prior={s.prior:<3}{flag}  {s.name}")
        print(f"\n{len(specs)} sources")
        return 0
    if args.action == "export":
        out = export_engine_feeds(specs, cfg.resolve(args.out))
        print(f"wrote {len(specs)} engine feeds to {out}")
        return 0
    # check
    if args.only:
        specs = [s for s in specs if s.id in set(args.only)]
    results = check_sources(specs, cfg.settings.collection.user_agent, cfg.settings.collection.http_timeout_seconds)
    bad = quiet = 0
    for r in results:
        if r["error"].startswith("local file"):
            mark = "-- "
        elif r["status"] == 200 and r["items"] > 0:
            mark = "ok "
        elif r["status"] == 200:
            mark, quiet = "~~ ", quiet + 1  # reachable but nothing new right now (sporadic streams)
        else:
            mark, bad = "!! ", bad + 1
        print(f"{mark}{r['id']:32} status={r['status']} items={r['items']:<4} {r['error']}")
    print(f"\n{len(results)} checked, {bad} failing, {quiet} quiet (reachable, no items right now)")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracker", description="News & Election Tracker")
    parser.add_argument("--config", help="profile directory (default: ./config or $TRACKER_CONFIG_DIR)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="show version and active profile").set_defaults(func=cmd_version)
    sub.add_parser("config", help="print resolved settings").set_defaults(func=cmd_config)

    p = sub.add_parser("sources", help="list, check or export the source registry")
    p.add_argument("action", choices=["list", "check", "export"])
    p.add_argument("--all", action="store_true", help="include disabled sources")
    p.add_argument("--only", nargs="*", help="check only these source ids")
    p.add_argument("--out", default="build/engine_feeds.yaml", help="export path (relative to project root)")
    p.set_defaults(func=cmd_sources)
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
