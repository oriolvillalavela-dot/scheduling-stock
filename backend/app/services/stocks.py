from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
except Exception:
    Chem = None
    Descriptors = None

from .loader import data

FINAL_STOCK_VOL_ML = 0.8  # fixed total volume for every stock

@dataclass
class Plan:
    name: str
    mw: Optional[float]
    eq: float
    stock_M: float
    uses: int
    per_well_uL: Optional[float]
    total_mass_mg: Optional[float]
    total_volume_mL: Optional[float]

def mw_from_smiles(smi: Optional[str]) -> Optional[float]:
    # Robustly ignore None/NaN/'nan' and only attempt parse on real strings
    if smi is None or Chem is None or Descriptors is None:
        return None
    if isinstance(smi, float):
        return None
    if isinstance(smi, str):
        if smi.strip() == "" or smi.strip().lower() == "nan":
            return None
    mol = Chem.MolFromSmiles(smi.strip())
    return None if mol is None else float(Descriptors.MolWt(mol))

def _col(df, name, alts):
    cols = {c.lower(): c for c in df.columns}
    for k in [name.lower(), *[a.lower() for a in alts]]:
        if k in cols: return cols[k]
    return None

def _norm(s: str) -> str:
    return ''.join(ch for ch in s.lower() if ch.isalnum())

def _well_sort_key(well: str):
    if not isinstance(well, str): well = str(well)
    well = well.strip().upper()
    rows = {"A":0,"B":1,"C":2,"D":3}
    r = rows.get(well[:1], 0)
    try:
        c = int(well[1:]) - 1
    except:
        c = 0
    return (r, c)

def stock_plan(day: int, include_next: bool, settings: dict, other_list: List[Dict]):
    df = data.df_reac
    if df is None:
        raise RuntimeError("Data not loaded")

    c_day   = _col(df, "day_number", ["day number", "day"])
    c_plate = _col(df, "plate_in_day", ["plate in day","plate"])
    c_ctrl  = _col(df, "is_control", ["control", "is control"])
    c_aryl  = _col(df, "Aryl-ID", ["aryl-id", "aryl_id", "aryl"])
    c_alk   = _col(df, "Alkyl-ID", ["alkyl-id", "alkyl_id", "alkyl"])
    c_well  = _col(df, "well", ["well position", "well_position", "pos"])

    days = [day] + ([day+1] if include_next else [])
    df_sub = df[df[c_day].isin(days)].copy()
    if not settings.get('include_controls', False) and c_ctrl:
        df_sub = df_sub[~df_sub[c_ctrl]]

    # Inputs
    eqA = float(settings.get('eq_aryl', 1))
    eqL = float(settings.get('eq_alkyl', 1.5))
    M_aryl = float(settings.get('M_aryl', 0.0313))
    M_alk  = float(settings.get('M_alkyl', 0.047))
    # NEW: basis in mmol per well (constant across all wells)
    mmol_basis = float(settings.get('mmol_limitant_per_well', 0.0005))
    basis_mol = mmol_basis / 1000.0  # mol per well

    # Determine limiting reagent (one with eq == 1)
    limiting_kind = None
    limiting_other_name = None
    if abs(eqA - 1.0) < 1e-9:
        limiting_kind = "aryl"
    elif abs(eqL - 1.0) < 1e-9:
        limiting_kind = "alkyl"
    else:
        for o in other_list:
            if abs(float(o.get('eq', 0)) - 1.0) < 1e-9:
                limiting_kind = "other"
                limiting_other_name = o.get('name', '').strip()
                break
    if limiting_kind is None:
        limiting_kind = "aryl"

    # MW maps (for stock mass calculations only)
    aryl_ids = df_sub[c_aryl].dropna().astype(str).unique().tolist()
    aryl_mw: Dict[str, Optional[float]] = {aid: mw_from_smiles(data.smiles_for_aryl(aid)) for aid in aryl_ids}

    alkyl_ids = df_sub[c_alk].dropna().astype(str).unique().tolist()
    def mw_for_alk(alk_id: str) -> Optional[float]:
        mw_over = data.mw_override_for_reagent(alk_id)
        if mw_over is not None: return mw_over
        smi = data.smiles_for_alkyl(alk_id)
        return mw_from_smiles(smi)
    alkyl_mw: Dict[str, Optional[float]] = {lid: mw_for_alk(lid) for lid in alkyl_ids}

    other_mw: Dict[str, Optional[float]] = {}
    for o in other_list:
        nm = o.get('name', '').strip()
        if not nm: continue
        mw_over = data.mw_override_for_reagent(nm)
        if mw_over is not None:
            other_mw[nm] = mw_over
        else:
            smi = o.get('smiles') or data.smiles_for_reagent(nm)
            other_mw[nm] = mw_from_smiles(smi)

    # Aggregate Aryl stocks
    aryl_rows: List[Plan] = []
    for aid, g in df_sub.groupby(c_aryl, dropna=True):
        mw = aryl_mw.get(str(aid))
        uses = int(g.shape[0])
        per_well_uL = (eqA * basis_mol / M_aryl) * 1e6 if M_aryl > 0 else None
        mass_mg = None if (mw is None) else (M_aryl * FINAL_STOCK_VOL_ML / 1000.0 * mw * 1000.0)
        aryl_rows.append(Plan(
            name=str(aid),
            mw=None if mw is None else round(mw, 3),
            eq=eqA, stock_M=M_aryl, uses=uses,
            per_well_uL=None if per_well_uL is None else round(per_well_uL, 2),
            total_mass_mg=None if mass_mg is None else round(mass_mg, 2),
            total_volume_mL=FINAL_STOCK_VOL_ML
        ))

    # Aggregate Alkyl stocks
    alkyl_rows: List[Plan] = []
    for lid, g in df_sub.groupby(c_alk, dropna=True):
        mw = alkyl_mw.get(str(lid))
        uses = int(g.shape[0])
        per_well_uL = (eqL * basis_mol / M_alk) * 1e6 if M_alk > 0 else None
        mass_mg = None if (mw is None) else (M_alk * FINAL_STOCK_VOL_ML / 1000.0 * mw * 1000.0)
        alkyl_rows.append(Plan(
            name=str(lid),
            mw=None if mw is None else round(mw, 3),
            eq=eqL, stock_M=M_alk, uses=uses,
            per_well_uL=None if per_well_uL is None else round(per_well_uL, 2),
            total_mass_mg=None if mass_mg is None else round(mass_mg, 2),
            total_volume_mL=FINAL_STOCK_VOL_ML
        ))

    # Other reagents (not mixed pair)
    other_rows: List[Plan] = []
    n_wells = int(df_sub.shape[0])
    def find_obj(label: str):
        for o in other_list:
            if _norm(o.get('name','')) == _norm(label):
                return o
        return None
    ni = find_obj('NiCl2')
    bpy = find_obj('dtbbpy')
    mixed_names = set()
    if ni and bpy:
        mixed_names = {_norm('NiCl2'), _norm('dtbbpy')}

    for obj in other_list:
        nm = obj.get('name', '').strip()
        if not nm or _norm(nm) in mixed_names:  # handled in mix
            continue
        eq = float(obj.get('eq', 1))
        M  = float(obj.get('M', 0))
        mwR = other_mw.get(nm)
        per_well_uL = (eq * basis_mol / M) * 1e6 if M > 0 else None
        mass_mg = None if (mwR is None) else (M * FINAL_STOCK_VOL_ML / 1000.0 * mwR * 1000.0)
        other_rows.append(Plan(
            name=nm, mw=None if mwR is None else round(mwR,3),
            eq=eq, stock_M=M, uses=n_wells,
            per_well_uL=None if per_well_uL is None else round(per_well_uL, 2),
            total_mass_mg=None if mass_mg is None else round(mass_mg, 2),
            total_volume_mL=FINAL_STOCK_VOL_ML
        ))

    # Mixed NiCl2 + dtbbpy stock
    mix = None
    if ni and bpy:
        mw_ni = other_mw.get(ni['name'])
        mw_bp = other_mw.get(bpy['name'])
        eq_ni = float(ni.get('eq', 1)); M_ni = float(ni.get('M', 0))
        eq_bp = float(bpy.get('eq', 1)); M_bp = float(bpy.get('M', 0))

        v_ni = (eq_ni * basis_mol / M_ni) * 1e6 if M_ni > 0 else 0.0
        v_bp = (eq_bp * basis_mol / M_bp) * 1e6 if M_bp > 0 else 0.0
        V_mix = max(v_ni, v_bp) if (v_ni or v_bp) else 0.0

        C_ni_mix = (eq_ni * basis_mol / (V_mix * 1e-6)) if (V_mix and V_mix > 0) else 0.0
        C_bp_mix = (eq_bp * basis_mol / (V_mix * 1e-6)) if (V_mix and V_mix > 0) else 0.0

        mass_mg_ni = None if (mw_ni is None) else round(C_ni_mix * (FINAL_STOCK_VOL_ML/1000.0) * mw_ni * 1000.0, 2)
        mass_mg_bp = None if (mw_bp is None) else round(C_bp_mix * (FINAL_STOCK_VOL_ML/1000.0) * mw_bp * 1000.0, 2)

        mix = {
            "title": "Mixed stock (NiCl2 + dtbbpy)",
            "per_well_uL": round(V_mix, 2) if V_mix else None,
            "total_volume_mL": round(FINAL_STOCK_VOL_ML, 2),
            "components": [
                {
                    "name": ni['name'],
                    "mw_g_mol": None if mw_ni is None else round(mw_ni,3),
                    "mix_conc_M": round(C_ni_mix, 6) if C_ni_mix else None,
                    "total_mass_mg": mass_mg_ni,
                },
                {
                    "name": bpy['name'],
                    "mw_g_mol": None if mw_bp is None else round(mw_bp,3),
                    "mix_conc_M": round(C_bp_mix, 6) if C_bp_mix else None,
                    "total_mass_mg": mass_mg_bp,
                },
            ]
        }

    def to_dict(p: Plan):
        return {
            "id_or_name": p.name,
            "mw_g_mol": p.mw,
            "uses": p.uses,
            "eq": p.eq,
            "stock_M": p.stock_M,
            "per_well_uL": p.per_well_uL,
            "total_mass_mg": p.total_mass_mg,
            "total_volume_mL": p.total_volume_mL,
        }

    totals = {
        "aryl":  [to_dict(x) for x in aryl_rows],
        "alkyl": [to_dict(x) for x in alkyl_rows],
        "others":[to_dict(x) for x in other_rows],
        "mixed": mix
    }

    # --- Grids per plate, sorted by well (A1..A6, B1..B6, C1..C6, D1..D6) ---
    other_names_for_grid = [o['name'] for o in other_list if _norm(o.get('name','')) not in {_norm('NiCl2'), _norm('dtbbpy')}]
    base_columns = ["well", "aryl_id", "alkyl_id", "limiting_kind", "lim_mmol", "uL_aryl", "uL_alkyl"] + [f"uL_{nm}" for nm in other_names_for_grid]
    if mix:
        base_columns.append("uL_MIX(NiCl2+dtbbpy)")

    grids = []
    for plate_num, g in df_sub.groupby(c_plate):
        rows = []
        g_sorted = g.sort_values(by=c_well, key=lambda s: s.map(_well_sort_key))
        for _, r in g_sorted.iterrows():
            well = str(r[c_well]) if c_well else ""
            aid = str(r[c_aryl]) if pd.notna(r[c_aryl]) else ""
            lid = str(r[c_alk]) if pd.notna(r[c_alk]) else ""

            uL_aryl  = (eqA * basis_mol / M_aryl) * 1e6 if M_aryl > 0 and aid else 0.0
            uL_alkyl = (eqL * basis_mol / M_alk)  * 1e6 if M_alk  > 0 and lid else 0.0

            row = {
                "well": well,
                "aryl_id": aid,
                "alkyl_id": lid,
                "limiting_kind": limiting_kind if limiting_kind != "other" else f"other:{limiting_other_name}",
                "lim_mmol": round(mmol_basis, 6),
                "uL_aryl": round(uL_aryl, 2) if uL_aryl else 0.0,
                "uL_alkyl": round(uL_alkyl, 2) if uL_alkyl else 0.0,
            }
            for obj in other_list:
                nm = obj.get('name', '').strip()
                if not nm or _norm(nm) in {_norm('NiCl2'), _norm('dtbbpy')}:
                    continue
                eq = float(obj.get('eq', 1)); M = float(obj.get('M', 0))
                uL = (eq * basis_mol / M) * 1e6 if M > 0 else 0.0
                row[f"uL_{nm}"] = round(uL, 2) if uL else 0.0

            if mix:
                V_mix = totals["mixed"]["per_well_uL"]
                row["uL_MIX(NiCl2+dtbbpy)"] = V_mix if V_mix else 0.0

            rows.append(row)

        grids.append({"plate": int(plate_num), "columns": base_columns, "rows": rows})


    # --- Build summaries by chemical -> plate -> wells (ordered) ---
    def accumulate_summary(df_slice, id_col):
        # returns dict: chem_id -> { plate_num: [wells...] }
        out = {}
        if id_col is None: 
            return out
        # sort by plate then well order
        for plate_num, g in df_sub.groupby(c_plate):
            g_sorted = g.sort_values(by=c_well, key=lambda s: s.map(_well_sort_key))
            for _, r in g_sorted.iterrows():
                chem = r.get(id_col)
                if pd.isna(chem) or str(chem).strip() == "":
                    continue
                well = str(r[c_well])
                out.setdefault(str(chem), {}).setdefault(int(plate_num), []).append(well)
        return out

    summaries = {
        "aryl": accumulate_summary(df_sub, c_aryl),
        "alkyl": accumulate_summary(df_sub, c_alk),
    }

    return {"totals": totals, "grids": grids, "summaries": summaries}

