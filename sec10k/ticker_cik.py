from __future__ import annotations
from typing import Any

import os
from dotenv import load_dotenv

from .sec_client import SecClient


load_dotenv()

ticker_mapping_url = os.environ["SEC_TICKER_MAPPING_URL"]


def resolve_cik(args, client):
    if args.ticker:
        return resolve_cik_from_ticker(client, args.ticker)

    return str(int(str(args.cik).strip())).zfill(10)


def resolve_cik_from_ticker(client: SecClient, ticker: str) -> str:
    ticker = ticker.strip().upper()
    data: dict[str, Any] = client.get_json(ticker_mapping_url)
    for key, row in data.items():
        if str(row.get("ticker", "")).upper() == ticker:
            cik_int = int(row["cik_str"])
            return str(cik_int).zfill(10)

    raise RuntimeError(f"Ticker not found in SEC mapping: {ticker}")
