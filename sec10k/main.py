from __future__ import annotations

import argparse
from datetime import datetime, UTC
import os
import logging

from .sec_client import SecClient, SecClientConfig
from .ticker_cik import resolve_cik, resolve_cik_from_ticker
from .filing_finder import pick_latest_10k
from .converter import html_to_text
from .storage import make_output_dir, write_json, write_text
from .pdf_renderer import html_to_pdf

from dotenv import load_dotenv

load_dotenv()


SUBMISSIONS_URL_TEMPLATE = os.getenv("SEC_SUBMISSIONS_URL_TEMPLATE")
FILING_DOC_URL_TEMPLATE = os.getenv("SEC_FILING_DOC_URL_TEMPLATE")

def build_submissions_url(cik_10: str) -> str:
    if SUBMISSIONS_URL_TEMPLATE:
        return SUBMISSIONS_URL_TEMPLATE.format(cik_10=cik_10)
    

def build_filing_doc_url(cik_10: str, accession_number: str, primary_document: str) -> str:
    cik_no_zeros = str(int(cik_10)) 
    accession_no_dashes = accession_number.replace("-", "")
    if FILING_DOC_URL_TEMPLATE:
        return FILING_DOC_URL_TEMPLATE.format(cik_no_zeros=cik_no_zeros, accession_no_dashes=accession_no_dashes, primary_document=primary_document)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch latest SEC 10-K filing and convert to text.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ticker", 
                   help="Company ticker, e.g. AAPL")
    g.add_argument("--cik", 
                   help="Company CIK (10 digits or not), e.g. 320193 or 0000320193")
    p.add_argument("--user-agent",
                    required=True,
                    help="SEC requires a real User-Agent with contact info (email).")
    p.add_argument("--out", default="output",
                    help="Output directory (default: output)")
    p.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level: DEBUG, INFO, WARNING, ERROR",
    )

    return p.parse_args()


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    args = parse_args()

    setup_logging(args.log_level)
    log = logging.getLogger("sec10k")
    log.info("Starting SEC 10-K fetch")
    
    client = SecClient(SecClientConfig(user_agent=args.user_agent))

    log.info("Resolving CIK")
    cik_10 = resolve_cik(args, client)

    log.info("Fetching submissions json: cik=%s", cik_10)
    submissions_url = build_submissions_url(cik_10)
    submissions = client.get_json(submissions_url)

    filing = pick_latest_10k(submissions, allow_amended_fallback=True)
    log.info(
        "Picked filing: form=%s filing_date=%s accession=%s primary_doc=%s",
        filing.form,
        filing.filing_date,
        filing.accession_number,
        filing.primary_document,
    )
    log.info("Fetching filing document")
    doc_url = build_filing_doc_url(filing.cik, filing.accession_number, filing.primary_document)

    html = client.get_text(doc_url)
    log.info("Converting HTML to text")
    text = html_to_text(html)
    out_dir = make_output_dir(args.out, filing.cik, filing.accession_number)
    log.info("Writing output: %s", out_dir)
    metadata = {
        "company": filing.company_name,
        "cik": filing.cik,
        "form": filing.form,
        "filing_date": filing.filing_date,
        "accession_number": filing.accession_number,
        "primary_document": filing.primary_document,
        "source_urls": {
            "submissions": submissions_url,
            "filing_document": doc_url,
        },
        "fetched_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "outputs": {
            "html":"filing.html",
            "text": "filing.txt",
            "pdf": "filing.pdf",
        },
    }

    write_json(out_dir / "metadata.json", metadata)
    write_text(out_dir / "filing.html", html)
    write_text(out_dir / "filing.txt", text)
    
    pdf_path = out_dir / "filing.pdf"
    log.info("Writing PDF: %s", pdf_path)
    html_to_pdf(out_dir / "filing.html", pdf_path)


    log.info("Done")
    

if __name__ == "__main__":
    main()
