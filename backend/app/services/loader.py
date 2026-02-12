import os
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, Any

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE), "data")

def _col(df, name, alts):
    cols = {c.lower(): c for c in df.columns}
    for k in [name.lower(), *[a.lower() for a in alts]]:
        if k in cols:
            return cols[k]
    return None

def _normalize_chemicals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a sheet that may have two SMILES columns (one for aryl, one for alkyl)
    into a tidy table with columns: ID | Type (aryl/alkyl) | SMILES.

    Expected wide format columns (case-insensitive):
      Aryl-ID | SMILES | Alkyl-ID | SMILES.1  (pandas usually renames the 2nd as 'SMILES.1')
    """
    if df is None or df.empty:
        return df

    cols = {c.lower(): c for c in df.columns}
    have = set(cols.keys())

    # Common case: two SMILES columns -> 'smiles' and 'smiles.1' (or 'smiles_1')
    if {"aryl-id", "smiles", "alkyl-id"}.issubset(have) and ("smiles.1" in have or "smiles_1" in have):
        a_id = cols["aryl-id"]
        a_sm = cols["smiles"]  # aryl smiles
        l_id = cols["alkyl-id"]
        l_sm = cols.get("smiles.1") or cols.get("smiles_1")  # alkyl smiles

        df_aryl = (
            df[[a_id, a_sm]]
            .rename(columns={a_id: "ID", a_sm: "SMILES"})
            .assign(Type="aryl")
        )
        df_alk = (
            df[[l_id, l_sm]]
            .rename(columns={l_id: "ID", l_sm: "SMILES"})
            .assign(Type="alkyl")
        )

        out = pd.concat([df_aryl, df_alk], ignore_index=True)

        # Clean
        out = out[~out["ID"].isna()].copy()
        out["ID"] = out["ID"].astype(str).str.strip()
        out["SMILES"] = out["SMILES"].astype(str).str.strip()
        out["Type"] = out["Type"].astype(str).str.strip().str.lower()

        # Remove literal "nan" strings
        out = out[(out["ID"] != "nan") & (out["SMILES"] != "nan")].copy()

        # Optional: quick validations
        dups = out.groupby(["ID", "Type"], dropna=False).size()
        if (dups > 1).any():
            print("[chemicals.xlsx] Warning: duplicated (ID,Type) rows:\n", dups[dups > 1])
        missing = out["SMILES"].eq("").sum()
        if missing:
            print(f"[chemicals.xlsx] Warning: {missing} rows with empty SMILES after normalization.")

        return out

    # Already tidy? Standardize casing/names
    if {"id", "type", "smiles"}.issubset(have):
        out = df.rename(columns={
            cols["id"]: "ID",
            cols["type"]: "Type",
            cols["smiles"]: "SMILES",
        }).copy()
        out["ID"] = out["ID"].astype(str).str.strip()
        out["SMILES"] = out["SMILES"].astype(str).str.strip()
        out["Type"] = out["Type"].astype(str).str.strip().str.lower()
        out = out[(out["ID"] != "") & (out["SMILES"] != "")]
        return out

    # Fallback: return as-is (lookups might not work), but warn once
    print("[chemicals.xlsx] Warning: could not normalize; expected columns not found.")
    return df.copy()

@dataclass
class PlateQuery:
    day: int
    plate_in_day: int

class Data:
    def __init__(self):
        self.df_reac: Optional[pd.DataFrame] = None
        self.df_chems: Optional[pd.DataFrame] = None
        self.df_reagents: Optional[pd.DataFrame] = None

        self.overrides_mw = {"Ir Cat": 1121.91}
        self.overrides_smiles = {
            "TTMSS": "C[Si](C)(C)[SiH]([Si](C)(C)C)[Si](C)(C)C",
            "AL-CONTROL": "O=C(OC(C)(C)C)N1CC(Br)C1",
        }

    def load_all(self):
        self.df_reac = self._load_excel(os.path.join(DATA_DIR, "reactions.xlsx"))
        self.df_chems = self._load_excel(os.path.join(DATA_DIR, "chemicals.xlsx"))
        self.df_reagents = self._load_excel(os.path.join(DATA_DIR, "reagents.xlsx"))

        # 🔧 Normalize chemicals.xlsx to (ID, Type, SMILES)
        if self.df_chems is not None:
            self.df_chems = _normalize_chemicals(self.df_chems)

        if self.df_reac is None:
            self.df_reac = self._demo_reactions()
        if self.df_chems is None:
            self.df_chems = self._demo_chemicals()
        if self.df_reagents is None:
            self.df_reagents = self._demo_reagents()

    def _load_excel(self, path) -> Optional[pd.DataFrame]:
        try:
            if os.path.exists(path):
                return pd.read_excel(path)
        except Exception as e:
            print(f"[loader] Failed to read {path}: {e}")
            return None
        return None

    def smiles_for_aryl(self, ar_id: str) -> Optional[str]:
        if self.df_chems is None:
            return None
        df = self.df_chems
        c_id = _col(df, "ID", ["id", "cpp_id", "aryl-id", "aryl_id"])
        c_sm = _col(df, "SMILES", ["smiles"])
        c_kind = _col(df, "Type", ["type", "class", "category"])
        if c_id and c_sm and c_kind:
            r = df[
                (df[c_id].astype(str).str.strip() == str(ar_id).strip())
                & (df[c_kind].astype(str).str.lower() == "aryl")
            ]
            if not r.empty:
                return str(r.iloc[0][c_sm])
        return None

    def smiles_for_alkyl(self, al_id: str) -> Optional[str]:
        if self.df_chems is None:
            return None
        df = self.df_chems
        c_id = _col(df, "ID", ["id", "alkyl-id", "alkyl_id"])
        c_sm = _col(df, "SMILES", ["smiles"])
        c_kind = _col(df, "Type", ["type", "class", "category"])
        if c_id and c_sm and c_kind:
            r = df[
                (df[c_id].astype(str).str.strip() == str(al_id).strip())
                & (df[c_kind].astype(str).str.lower() == "alkyl")
            ]
            if not r.empty:
                return str(r.iloc[0][c_sm])
        return None

    def smiles_for_reagent(self, name: str) -> Optional[str]:
        nm = (name or "").strip()
        if nm in self.overrides_smiles:
            return self.overrides_smiles[nm]
        if self.df_reagents is None:
            return None
        df = self.df_reagents
        c_nm = _col(df, "Name", ["name", "reagent", "id"])
        c_sm = _col(df, "SMILES", ["smiles"])
        if c_nm and c_sm:
            r = df[df[c_nm].astype(str).str.strip().str.lower() == nm.lower()]
            if not r.empty:
                return str(r.iloc[0][c_sm])
        return None

    def mw_override_for_reagent(self, name: str):
        return self.overrides_mw.get(name)

    def plate_grid(self, q: PlateQuery):
        df = self.df_reac
        c_day = _col(df, "day_number", ["day number", "day"])
        c_plate = _col(df, "plate_in_day", ["plate in day", "plate"])
        c_well = _col(df, "well", ["well position", "well_position", "pos"])
        c_ctrl = _col(df, "is_control", ["control", "is control"])
        c_aryl = _col(df, "Aryl-ID", ["aryl-id", "aryl_id", "aryl"])
        c_alk = _col(df, "Alkyl-ID", ["alkyl-id", "alkyl_id", "alkyl"])

        sub = df[(df[c_day] == q.day) & (df[c_plate] == q.plate_in_day)].copy()
        cells = []
        rows = {"A": 0, "B": 1, "C": 2, "D": 3}
        for _, r in sub.iterrows():
            well = str(r[c_well]).strip().upper()
            row = rows.get(well[:1], 0)
            try:
                col = int(well[1:]) - 1
            except Exception:
                col = 0
            if c_ctrl and bool(r[c_ctrl]):
                label = "CONTROL"
                control = True
            else:
                a = str(r[c_aryl]) if c_aryl else ""
                l = str(r[c_alk]) if c_alk else ""
                label = f"{a}/{l}".strip(" /")
                control = False
            cells.append({"r": row, "c": col, "label": label, "control": control})
        return {"rows": 4, "cols": 6, "cells": cells}

    def _demo_reactions(self):
        data = []
        rows = ["A", "B", "C", "D"]
        idx = 0
        for day in [1, 2]:
            for plate in [1, 2]:
                for r in range(4):
                    for c in range(6):
                        well = f"{rows[r]}{c+1}"
                        is_ctrl = (r == 0 and c == 0)
                        ar = f"AR-{idx%8+1:03d}"
                        al = f"AL-{(idx*3)%9+1:03d}"
                        data.append({
                            "day_number": day,
                            "plate_in_day": plate,
                            "well": well,
                            "is_control": is_ctrl,
                            "Aryl-ID": ar,
                            "Alkyl-ID": al
                        })
                        idx += 1
        return pd.DataFrame(data)

    def _demo_chemicals(self):
        return pd.DataFrame([
            {"ID": "AR-001", "Type": "aryl", "SMILES": "c1ccccc1Br"},
            {"ID": "AR-002", "Type": "aryl", "SMILES": "c1cc(Br)ccc1C"},
            {"ID": "AL-001", "Type": "alkyl", "SMILES": "CCCCBr"},
            {"ID": "AL-002", "Type": "alkyl", "SMILES": "CC(C)CBr"},
            {"ID": "AL-CONTROL", "Type": "alkyl", "SMILES": "O=C(OC(C)(C)C)N1CC(Br)C1"}
        ])

    def _demo_reagents(self):
        return pd.DataFrame([
            {"Name": "TTMSS", "SMILES": "C[Si](C)(C)[SiH]([Si](C)(C)C)[Si](C)(C)C"},
            {"Name": "NiCl2", "SMILES": ""},
            {"Name": "Ir Cat", "SMILES": ""},
            {"Name": "dtbbpy", "SMILES": ""}
        ])

data = Data()
