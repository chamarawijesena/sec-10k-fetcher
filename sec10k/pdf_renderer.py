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

        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(prefer_css_page_size=False)


        page.add_style_tag(content="""
        @media print {
        @page {
            size: auto;
        }

    """)

        page.pdf(
            path=str(pdf_path),
            format="Letter",          
            prefer_css_page_size=True,
            print_background=True,
        )

        page.close()
        browser.close()
