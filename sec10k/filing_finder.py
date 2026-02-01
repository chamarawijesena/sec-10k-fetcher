from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

sec_10k_forms = tuple(
    form.strip()
    for form in os.environ["SEC_10K_FORMS"].split(",")
    if form.strip()
)

@dataclass(frozen=True)
class FilingMetadata:
    cik: str                  
    company_name: str
    form: str                
    filing_date: str         
    accession_number: str    
    primary_document: str     

def pick_latest_10k(submissions: dict[str, Any], *, allow_amended_fallback: bool = True) -> FilingMetadata:

    cik = str(submissions.get("cik", "")).zfill(10)
    company_name = submissions.get("name", "") or submissions.get("entityName", "") or "Unknown"

    recent = (submissions.get("filings", {}) or {}).get("recent", {}) or {}
    forms = recent.get("form", []) or []
    dates = recent.get("filingDate", []) or []
    accessions = recent.get("accessionNumber", []) or []
    primary_docs = recent.get("primaryDocument", []) or []

    if not (len(forms) == len(dates) == len(accessions) == len(primary_docs)):
        raise RuntimeError("Unexpected submissions JSON shape: recent filings arrays have mismatched lengths")

    idx_10k = None

    for i, form in enumerate(sec_10k_forms):
        if i > 0 and not allow_amended_fallback:
            break

        idx_10k = _first_index(forms, form)
        if idx_10k is not None:
            break

    if idx_10k is None:
        raise RuntimeError("No 10-K (or 10-K/A) found in recent filings for this company")

    return FilingMetadata(
        cik=cik,
        company_name=company_name,
        form=forms[idx_10k],
        filing_date=dates[idx_10k],
        accession_number=accessions[idx_10k],
        primary_document=primary_docs[idx_10k],
    )


def _first_index(items: list[str], target: str) -> Optional[int]:
    # recent filings are typically sorted newest-first, so first match is the latest
    for i, v in enumerate(items):
        if v == target:
            return i
    return None
