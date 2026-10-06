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


def cmd_watch(args, cfg) -> int:
    from tracker.watch import load_watch_pages, run_watch

    pages = load_watch_pages(cfg.config_dir)
    if args.only:
        pages = [p for p in pages if p.id in set(args.only)]
    results = run_watch(pages, cfg.settings.collection.user_agent, cfg.settings.collection.http_timeout_seconds)
    failed = [r for r in results if not r.ok]
    print(f"{len(results)} pages: {sum(r.new for r in results)} new items, "
          f"{sum(r.baseline for r in results)} baselines, {len(failed)} failed")
    return 1 if failed and len(failed) == len(results) else 0


def make_bot(cfg):
    import httpx

    from tracker.bot import Bot
    from tracker.db import connect
    from tracker.telegram import TelegramClient

    from tracker.commands import build_commands

    client = TelegramClient(cfg.secrets.telegram_bot_token)
    http = httpx.Client(headers={"User-Agent": cfg.settings.collection.user_agent}, timeout=15, follow_redirects=True)
    return Bot(client, connect(cfg.db_path), cfg.secrets.telegram_allowed_chat_ids, http=http,
               commands=build_commands(cfg), public=cfg.settings.telegram.public)


def cmd_bot(args, cfg) -> int:
    from tracker.bot import Card

    if not cfg.secrets.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not set; skipping the bot.")
        return 0
    bot = make_bot(cfg)
    if args.action == "poll":
        print(bot.poll_once())
    elif args.action == "listen":
        print("Listening for Telegram updates (Ctrl+C to stop)...")
        try:
            while True:
                stats = bot.poll_once(long_poll_seconds=50)
                if stats["updates"]:
                    log.info("processed %s", stats)
        except KeyboardInterrupt:
            pass
    elif args.action == "test-card":
        card = Card(url="https://www.ugc.gov.in/", title="Test card: tap a button to check training works",
                    feed_id="official-ugc", source_name="UGC — notices", meta="National · Higher education · Policy")
        for chat_id in cfg.secrets.telegram_allowed_chat_ids:
            bot.send_cards(chat_id, [card])
        print(f"sent to {len(cfg.secrets.telegram_allowed_chat_ids)} chat(s)")
    return 0


def cmd_process(args, cfg) -> int:
    from tracker.process import process

    report = process(cfg, mode=args.mode)
    print(f"run {report.run_id} via {report.mode}: {report.seen} items, {report.new} new, "
          f"{report.relevant} core+relevant, bands={report.bands}")
    if report.errors:
        print(f"{len(report.errors)} source errors: " + ", ".join(sorted(report.errors)))
    return 0


def cmd_train(args, cfg) -> int:
    from tracker.db import connect
    from tracker.learn import RelevanceModel, train

    info = train(connect(cfg.db_path), cfg.config_dir)
    if info is None:
        print("Not enough labels yet (need both relevant and not-relevant examples).")
        return 0
    model = RelevanceModel.load(cfg.settings.relevance.model)
    print(f"trained on {info.labels} client labels + {info.seed_labels} seed labels "
          f"({info.positives} relevant / {info.negatives} not); cv accuracy={info.cv_accuracy}, "
          f"cv precision={info.cv_precision}; model weight in scoring={model.weight:.2f}")
    return 0


def cmd_report(args, cfg) -> int:
    from tracker.commands import story_card
    from tracker.reports import build_report, render, send_email, telegram_text, write_report

    data = build_report(cfg, args.kind)
    files = write_report(cfg, data)
    print(f"{data.title} ({data.period_label}): {data.stats['stories']} stories, {data.stats['core']} core")
    for name, path in files.items():
        print(f"  {name:9} {path}")
    send = args.send
    conn = None
    if send:
        from tracker.db import connect
        from tracker.reports import mark_sent, should_send

        conn = connect(cfg.db_path)
        send, why = should_send(conn, args.kind, args.once_after)
        print(f"  send: {'yes' if send else 'no'} ({why})")
    if send:
        subject = f"{'Weekly' if args.kind == 'weekly' else 'Daily'} brief — {data.period_label}"
        exec_to = cfg.secrets.report_email_to_exec or cfg.secrets.report_email_to
        send_email(cfg, subject, render(data, "brief.html"), exec_to)
        attachments = [files["excel"]] if args.kind == "weekly" else []
        send_email(cfg, f"Analyst digest — {data.period_label}", render(data, "digest.html"),
                   cfg.secrets.report_email_to, attachments)
        if cfg.secrets.telegram_bot_token:
            from tracker.reports import telegram_caption

            bot = make_bot(cfg)
            cards = [story_card(s) for s in data.top[: cfg.settings.telegram.brief_max_items]]
            # The formatted brief as a PDF document with a short caption; plain text if no PDF was made.
            documents = [(files["pdf"], telegram_caption(data))] if "pdf" in files else []
            if args.kind == "weekly":
                documents.append((files["excel"], "Weekly workbook: state × sector pivot and trackers"))
            recipients = bot.recipients()
            reached = bot.broadcast(documents, cards, text="" if "pdf" in files else telegram_text(data))
            print(f"  sent to {reached} of {len(recipients)} Telegram chat(s)")
            if reached:  # if nobody was reached, the next scheduled attempt tries again
                mark_sent(conn, args.kind)
    return 0


def cmd_site(args, cfg) -> int:
    from tracker.site import build_site

    path = build_site(cfg)
    print(f"dashboard written to {path}")
    return 0


def cmd_run(args, cfg) -> int:
    """One scheduled pass: watch official pages → Telegram updates → process → dashboard.

    Each step is isolated so one failing source or service never stops the rest; the exit code
    is non-zero only if processing itself fails (that is what the run log must show).
    """
    from tracker.db import connect
    from tracker.process import process
    from tracker.site import build_site
    from tracker.watch import load_watch_pages, run_watch

    def step(name, fn):
        try:
            result = fn()
            log.info("step %s: ok %s", name, result if result is not None else "")
            return True
        except Exception as exc:  # keep going; the error is logged and visible in the Actions log
            log.error("step %s failed: %s: %s", name, type(exc).__name__, exc)
            return False

    c = cfg.settings.collection
    step("watch", lambda: sum(r.new for r in run_watch(load_watch_pages(cfg.config_dir), c.user_agent,
                                                          c.http_timeout_seconds)))
    if cfg.secrets.telegram_bot_token:
        step("telegram", lambda: make_bot(cfg).poll_once())
    ok = step("process", lambda: process(cfg, mode=args.mode).bands)
    step("site", lambda: build_site(cfg))
    conn = connect(cfg.db_path)  # fold the write-ahead log into the file before it is saved
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    return 0 if ok else 1


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

    p = sub.add_parser("watch", help="check official pages for new notices and PDFs")
    p.add_argument("--only", nargs="*", help="watch only these page ids")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("bot", help="Telegram bot: process updates once, listen continuously, or send a test card")
    p.add_argument("action", choices=["poll", "listen", "test-card"])
    p.set_defaults(func=cmd_bot)

    p = sub.add_parser("process", help="gather items, tag and score them, save to the tracker database")
    p.add_argument("--mode", choices=["auto", "engine", "direct"], default="auto",
                   help="auto = engine output if present, else fetch feeds directly")
    p.set_defaults(func=cmd_process)

    sub.add_parser("train", help="retrain the relevance model from feedback and seed labels").set_defaults(func=cmd_train)

    p = sub.add_parser("report", help="build the daily or weekly report (HTML, Excel, Telegram text)")
    p.add_argument("kind", choices=["daily", "weekly"])
    p.add_argument("--send", action="store_true", help="also deliver by email and Telegram (if configured)")
    p.add_argument("--once-after", metavar="HH:MM",
                   help="with --send: send only once per day/week, and not before this IST time (for scheduled runs)")
    p.set_defaults(func=cmd_report)

    sub.add_parser("site", help="build the static dashboard (output/site/index.html)").set_defaults(func=cmd_site)

    p = sub.add_parser("run", help="one scheduled pass: watch, Telegram, process, dashboard")
    p.add_argument("--mode", choices=["auto", "engine", "direct"], default="auto")
    p.set_defaults(func=cmd_run)
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
