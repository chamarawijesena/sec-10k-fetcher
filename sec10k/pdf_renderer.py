from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    html_path = html_path.resolve()
    pdf_path = pdf_path.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(html_path.as_uri(), wait_until="domcontentloaded")

        page.pdf(
            path=str(pdf_path),
            format="Letter",          
            print_background=True,
            margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
        )

        browser.close()
