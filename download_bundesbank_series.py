"""Download raw Bundesbank time series listed in an Excel workbook.

This script expects an Excel file that contains Bundesbank indicator codes
in a sheet named "Abhängige Variablen" (or a custom sheet). For each
indicator code it builds the corresponding Bundesbank download URL and
stores the CSV data in a target directory.
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

import pandas as pd
import requests


BUNDESBANK_BASE = "https://api.statistiken.bundesbank.de/rest/download"


def read_indicator_codes(excel_file: str, sheet: str = "Abhängige Variablen",
                         column: str = "indicator_code") -> list[str]:
    """Return a list of indicator codes from *excel_file*.

    Parameters
    ----------
    excel_file: Path to the Excel file.
    sheet:     Sheet name that contains the codes.
    column:    Column name holding Bundesbank indicator codes.
    """
    df = pd.read_excel(excel_file, sheet_name=sheet)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in sheet '{sheet}'.")
    return df[column].dropna().unique().tolist()


def download_series(indicator_code: str, out_dir: str) -> str:
    """Download a single Bundesbank time series as CSV.

    The *indicator_code* usually looks like "BBBK1.M.OUA249" where
    the part before the first dot denotes the dataset and the remainder
    encodes the series. The downloaded file is stored in *out_dir* and the
    path to the written file is returned.
    """
    dataset, series = indicator_code.split(".", 1)
    url = f"{BUNDESBANK_BASE}/{dataset}/{series}?format=csv&lang=de"
    os.makedirs(out_dir, exist_ok=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    file_path = os.path.join(out_dir, f"{indicator_code.replace('.', '_')}.csv")
    with open(file_path, "wb") as fh:
        fh.write(response.content)
    return file_path


def download_all(codes: Iterable[str], out_dir: str) -> None:
    for code in codes:
        try:
            path = download_series(code, out_dir)
            print(f"Downloaded {code} -> {path}")
        except Exception as exc:  # pragma: no cover - simple logging
            print(f"Failed {code}: {exc}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download Bundesbank time series listed in an Excel sheet")
    parser.add_argument("excel", help="Excel file that contains indicator codes")
    parser.add_argument("--sheet", default="Abhängige Variablen", help="Sheet name with indicator codes")
    parser.add_argument("--column", default="indicator_code", help="Column name for indicator codes")
    parser.add_argument("--out", default="raw_data", help="Directory for downloaded CSV files")
    args = parser.parse_args(argv)

    codes = read_indicator_codes(args.excel, args.sheet, args.column)
    download_all(codes, args.out)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
