"""
Seeder for tercih statistics data.
Loads pre-cleaned CSV files into the database using bulk inserts.

Note: CSV files should be pre-cleaned using scripts/clean_tercih_csvs.py
"""

import csv
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.modules.tercih_stats.models import (
    ProgramPrice,
    TercihIstatistikleri,
    TercihPreference,
    TercihStats,
)


DATA_DIR = Path(__file__).parent.parent / "data"
TERCIH_DIR_2022_2024 = DATA_DIR / "tercih" / "2022-2024"
TERCIH_DIR_2025 = DATA_DIR / "tercih" / "2025"
PRICES_DIR = DATA_DIR / "prices" / "2024-2025"

BATCH_SIZE = 5000


def _val(value: str, dtype: str = "float") -> Any:
    """Convert CSV value to appropriate type."""
    if not value or value in ("", "nan", "None"):
        return None
    try:
        if dtype == "int":
            return int(float(value))
        elif dtype == "bool":
            return value.lower() == "true"
        return float(value)
    except ValueError:
        return None


def _load_csv(path: Path) -> list[dict]:
    """Load CSV file as list of dicts."""
    if not path.exists():
        print(f"Warning: {path} not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _bulk_insert(db: Session, model, records: list[dict]):
    """Bulk insert records."""
    if not records:
        return
    db.bulk_insert_mappings(model, records)
    db.commit()


def seed_program_prices(db: Session) -> int:
    """Seed program prices."""
    rows = _load_csv(PRICES_DIR / "prices_processed.csv")
    records = []
    
    for row in rows:
        if not row.get("yop_kodu"):
            continue
        records.append({
            "yop_kodu": row["yop_kodu"],
            "is_english": _val(row.get("is_english", ""), "bool"),
            "scholarship_pct": _val(row.get("scholarship_pct", "")),
            "full_price_2024": _val(row.get("full_price_2024", "")),
            "full_price_2025": _val(row.get("full_price_2025", "")),
            "discounted_price_2024": _val(row.get("discounted_price_2024", "")),
            "discounted_price_2025": _val(row.get("discounted_price_2025", "")),
        })
    
    _bulk_insert(db, ProgramPrice, records)
    print(f"Seeded {len(records)} program prices")
    return len(records)


def seed_tercih_stats(db: Session) -> int:
    """Seed tercih stats from combined_stats.csv files."""
    records = []
    
    for csv_path in [TERCIH_DIR_2022_2024 / "combined_stats.csv", TERCIH_DIR_2025 / "combined_stats.csv"]:
        for row in _load_csv(csv_path):
            yop_kodu = row.get("yop_kodu", "")
            year = _val(row.get("year", ""), "int")
            if not yop_kodu or not year:
                continue
            records.append({
                "yop_kodu": yop_kodu,
                "year": year,
                "ortalama_tercih_edilme_sirasi": _val(row.get("ortalama_tercih_edilme_sirasi_A", "")),
                "ortalama_yerlesen_tercih_sirasi": _val(row.get("ortalama_yerlesen_tercih_sirasi_B", "")),
                "marka_etkinlik_degeri": _val(row.get("marka_etkinlik_degeri_A_div_B", "")),
            })
    
    _bulk_insert(db, TercihStats, records)
    print(f"Seeded {len(records)} tercih stats")
    return len(records)


def seed_tercih_istatistikleri(db: Session) -> int:
    """Seed tercih istatistikleri - auto-map float columns from CSV headers."""
    # Define which columns are floats (all numeric columns)
    float_cols = [
        "bir_kontenjana_talip_olan_aday_sayisi_2022",
        "bir_kontenjana_talip_olan_aday_sayisi_2023",
        "bir_kontenjana_talip_olan_aday_sayisi_2024",
        "bir_kontenjana_talip_olan_aday_sayisi_2025",
        "ilk_uc_sirada_tercih_eden_sayisi_2022",
        "ilk_uc_sirada_tercih_eden_sayisi_2023",
        "ilk_uc_sirada_tercih_eden_sayisi_2024",
        "ilk_uc_sirada_tercih_eden_sayisi_2025",
        "ilk_uc_sirada_tercih_eden_orani_2022",
        "ilk_uc_sirada_tercih_eden_orani_2023",
        "ilk_uc_sirada_tercih_eden_orani_2024",
        "ilk_uc_sirada_tercih_eden_orani_2025",
        "ilk_uc_tercih_olarak_yerlesen_sayisi_2022",
        "ilk_uc_tercih_olarak_yerlesen_sayisi_2023",
        "ilk_uc_tercih_olarak_yerlesen_sayisi_2024",
        "ilk_uc_tercih_olarak_yerlesen_sayisi_2025",
        "ilk_uc_tercih_olarak_yerlesen_orani_2022",
        "ilk_uc_tercih_olarak_yerlesen_orani_2023",
        "ilk_uc_tercih_olarak_yerlesen_orani_2024",
        "ilk_uc_tercih_olarak_yerlesen_orani_2025",
    ]
    
    # Merge data from both files by yop_kodu
    merged = {}
    
    for csv_path in [TERCIH_DIR_2022_2024 / "istatistikleri.csv", TERCIH_DIR_2025 / "istatistikleri.csv"]:
        for row in _load_csv(csv_path):
            yop_kodu = row.get("yop_kodu", "")
            if not yop_kodu:
                continue
            
            if yop_kodu not in merged:
                merged[yop_kodu] = {"yop_kodu": yop_kodu}
            
            # Auto-map all float columns present in the row
            for col in float_cols:
                if col in row and row[col]:
                    merged[yop_kodu][col] = _val(row[col])
    
    records = list(merged.values())
    _bulk_insert(db, TercihIstatistikleri, records)
    print(f"Seeded {len(records)} tercih istatistikleri")
    return len(records)


def seed_tercih_preferences(db: Session) -> int:
    """Seed tercih preferences from all preference files."""
    pref_config = [
        ("selected_universities_iller.csv", "city", "il"),
        ("selected_universities_universiteler.csv", "university", "universite"),
        ("selected_universities_programlar.csv", "program", "program"),
    ]
    
    records = []
    
    for pref_dir in [TERCIH_DIR_2022_2024 / "preferences", TERCIH_DIR_2025 / "preferences"]:
        for filename, pref_type, item_col in pref_config:
            for row in _load_csv(pref_dir / filename):
                source_uni = row.get("source_university", "").strip()
                yop_kodu = row.get("yop_kodu", "")
                year = _val(row.get("year", ""), "int")
                preferred_item = row.get(item_col, "").strip()
                tercih_sayisi = _val(row.get("tercih_sayisi", ""), "int")
                
                if not all([source_uni, yop_kodu, year, preferred_item, tercih_sayisi]):
                    continue
                
                record = {
                    "source_university": source_uni,
                    "yop_kodu": yop_kodu,
                    "year": year,
                    "preference_type": pref_type,
                    "preferred_item": preferred_item,
                    "tercih_sayisi": tercih_sayisi,
                }
                if pref_type == "university":
                    record["university_type"] = row.get("university_type", "").strip() or None
                
                records.append(record)
                
                # Batch insert to avoid memory issues
                if len(records) >= BATCH_SIZE:
                    _bulk_insert(db, TercihPreference, records)
                    records = []
    
    # Insert remaining
    _bulk_insert(db, TercihPreference, records)
    total = db.query(TercihPreference).count()
    print(f"Seeded {total} tercih preferences")
    return total


def clear_tercih_data(db: Session):
    """Clear all tercih-related tables."""
    db.query(TercihPreference).delete()
    db.query(TercihIstatistikleri).delete()
    db.query(TercihStats).delete()
    db.query(ProgramPrice).delete()
    db.commit()
    print("Cleared all tercih data")


def seed_all_tercih_data(db: Session, clear_first: bool = True):
    """Seed all tercih data from CSV files."""
    if clear_first:
        clear_tercih_data(db)
    
    total = 0
    total += seed_program_prices(db)
    total += seed_tercih_stats(db)
    total += seed_tercih_istatistikleri(db)
    total += seed_tercih_preferences(db)
    
    print(f"Total tercih records seeded: {total}")
    return total


if __name__ == "__main__":
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        seed_all_tercih_data(db)
    finally:
        db.close()
