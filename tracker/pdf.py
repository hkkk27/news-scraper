"""Print an HTML report to PDF with a headless Chromium browser (Chrome, Edge, Chromium).

Chromium is already installed on GitHub's Ubuntu runners and on almost every Windows/macOS
machine, and it shapes Indian scripts correctly (conjuncts, matras), which pure-Python PDF
libraries do not. No extra Python dependency is needed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from tracker.log import get_logger

log = get_logger("tracker.pdf")

CANDIDATES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_browser() -> str | None:
    override = os.environ.get("CHROME_PATH", "").strip()
    for candidate in ([override] if override else []) + CANDIDATES:
        path = shutil.which(candidate) or (candidate if os.path.isfile(candidate) else None)
        if path:
            return path
    return None


def html_to_pdf(html_path: Path, pdf_path: Path, timeout: int = 120) -> Path | None:
    """Render `html_path` to `pdf_path`. Returns the PDF path, or None if no browser/failure."""
    browser = find_browser()
    if not browser:
        log.warning("no Chrome/Edge/Chromium found; PDF skipped (set CHROME_PATH)")
        return None
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    with tempfile.TemporaryDirectory() as profile:  # a throwaway profile never touches the user's browser
        command = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
                   f"--user-data-dir={profile}", "--no-pdf-header-footer", "--virtual-time-budget=5000",
                   f"--print-to-pdf={pdf_path.resolve()}", html_path.resolve().as_uri()]
        try:
            subprocess.run(command, capture_output=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            log.warning("PDF rendering failed: %s", exc)
            return None
    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        return pdf_path
    log.warning("PDF rendering produced no file (%s)", browser)
    return None
