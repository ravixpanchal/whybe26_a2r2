from __future__ import annotations

from typing import Any

import pandas as pd

from app.schemas.assessment import BorrowerInput


def borrower_to_frame(
    borrower: BorrowerInput, feature_order: list[str]
) -> pd.DataFrame:
    values = borrower.model_dump()
    unknown = set(values) - set(feature_order)
    missing = set(feature_order) - set(values)
    if unknown or missing:
        raise ValueError(
            f"Input feature contract mismatch; unknown={sorted(unknown)}, "
            f"missing={sorted(missing)}"
        )
    return pd.DataFrame([[values[name] for name in feature_order]], columns=feature_order)
