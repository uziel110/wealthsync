"""
Stub parser for Bank Hapoalim Excel exports.
Populate COLUMN_MAP once a real export is available.
"""

import pandas as pd
from io import BytesIO

COLUMN_MAP: dict[str, str] = {
    # "Hebrew header": "normalised_column",
}


def parse_hapoalim(file: BytesIO | str, account_name: str = "Hapoalim") -> pd.DataFrame:
    raise NotImplementedError(
        "Hapoalim parser is not yet implemented. "
        "Upload a sample export to build the column mapping."
    )
