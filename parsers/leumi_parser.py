"""
Stub parser for Bank Leumi Excel exports.
Populate COLUMN_MAP once a real export is available.
"""

import pandas as pd
from io import BytesIO

COLUMN_MAP: dict[str, str] = {
    # "Hebrew header": "normalised_column",
}


def parse_leumi(file: BytesIO | str, account_name: str = "Leumi") -> pd.DataFrame:
    raise NotImplementedError(
        "Bank Leumi parser is not yet implemented. "
        "Upload a sample export to build the column mapping."
    )
