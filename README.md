# SEC 10-K Fetcher (Document Automation)

This project is a small **data automation pipeline** that fetches the **latest 10-K filing** for a company from the **U.S. SEC EDGAR** system.

Given a company **ticker or CIK**, the tool identifies the most recent 10-K filing, downloads the primary filing document in **HTML**, converts it into **readable plain text**, renders a **PDF snapshot**, and stores all outputs together with structured metadata.

The HTML format is intentionally preserved alongside the converted text and PDF to support downstream use cases such as **NLP, document analysis, and archival**.

---

## Design Rationale

In addition to text extraction, the pipeline generates a **PDF representation** of the filing using a browser-based renderer. This provides a faithful, human-readable snapshot of the original document while keeping HTML as the canonical source for processing.

Each output includes metadata such as:
- Company name
- CIK
- Form type
- Accession number
- Filing date
- Source URLs
- Fetch timestamp (UTC)
- Generated output artifacts

In real-world data pipelines, this context is essential for **traceability, reproducibility, and downstream integration**.

---

## How It Works

1. Resolve a company **ticker → CIK** using the SEC ticker mapping.
2. Fetch the company submissions JSON from the SEC.
3. Select the most recent filing with `form == 10-K` (with an optional fallback to `10-K/A`).
4. Build the EDGAR document URL using the CIK, accession number, and primary document name.
5. Download the HTML filing.
6. Convert the HTML filing to clean plain text.
7. Render the HTML filing to a **PDF snapshot** using a headless browser.
8. Write all artifacts and metadata to disk.

---

## High-Level Architecture

```text
User / CLI
   |
   |  (ticker or CIK, user-agent)
   v
+---------------------+
|  sec10k.main        |
|  (CLI entrypoint)   |
+---------------------+
           |
           | resolves CIK
           v
+---------------------+
|  ticker_cik         |
|  - ticker → CIK     |
+---------------------+
           |
           | build SEC URLs
           v
+---------------------+
|  SecClient          |
|  - HTTP requests    |
|  - retries          |
|  - backoff          |
|  - rate-limit aware |
+---------------------+
      |           |
      |           |
      v           v
SEC Submissions   SEC Filing Document
JSON Endpoint     HTML Endpoint
(data.sec.gov)   (sec.gov/Archives)
      |
      v
+---------------------+
|  filing_finder      |
|  - select latest    |
|    10-K / 10-K/A    |
+---------------------+
           |
           v
+---------------------+
|  converter          |
|  - HTML → text      |
+---------------------+
           |
           v
+---------------------+
|  pdf_renderer       |
|  - HTML → PDF       |
|  (Playwright)       |
+---------------------+
           |
           v
+---------------------+
|  storage            |
|  - write metadata   |
|  - write outputs    |
|  (HTML / text / PDF)|
+---------------------+
           |
           v
Output Directory
(output/<CIK>/<accession>/)
```

---

## Installation

### Install dependencies using:

```bash
pip install -r requirements.txt
```
### Install the Playwright-managed Chromium browser (required for PDF rendering):

```bash
python -m playwright install chromium
```

### Running the Application

#### From the project root:

```bash
python -m sec10k.main \
  --ticker AAPL \
  --user-agent "Chamara Wijesena chamara.wijesena94@gmail.com"
```

#### With explicit log level:

```bash
python -m sec10k.main \
  --ticker AAPL \
  --user-agent "Chamara Wijesena chamara.wijesena94@gmail.com" \
  --log-level INFO
```

---

## Example Companies

The following examples can be used to try the tool with different well-known companies:

| Company         | Ticker |
|-----------------|--------|
| Apple           | AAPL   |
| Meta Platforms  | META   |
| Alphabet        | GOOGL  |
| Amazon          | AMZN   |
| Netflix         | NFLX   |
| Goldman Sachs   | GS     |

---

## Running Tests

### Tests are written using **pytest**.

#### From the project root, run:

```bash
python -m pytest
```

(Note: `python -m pytest` ensures pytest runs with the correct Python interpreter.)

---

## Output

All outputs are written to the `output/` directory and include:
- Raw HTML filing
- Converted plain-text filing
- Metadata JSON
