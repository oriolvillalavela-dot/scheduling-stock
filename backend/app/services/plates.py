from typing import Dict, Any
import pandas as pd
from ..services.loader import data

def get_plate_preview(plate_number: int) -> Dict[str, Any] | None:
    df = data.df_reac
    if df is None:
        raise RuntimeError("Data not loaded")
    sub = df[df["plate_number"] == plate_number].copy()
    if sub.empty:
        return None
    day = int(sub["day_number"].iloc[0])
    cells = []
    for _, r in sub.iterrows():
        cells.append({
            "well": str(r["well"]),
            "is_control": bool(r["is_control"]),
            "alkyl_id": None if bool(r["is_control"]) else (None if pd.isna(r.get("Alkyl-ID")) else str(r.get("Alkyl-ID"))),
            "aryl_id":  None if bool(r["is_control"]) else (None if pd.isna(r.get("Aryl-ID")) else str(r.get("Aryl-ID"))),
        })
    return {"plate_number": int(plate_number), "day_number": day, "cells": cells}
