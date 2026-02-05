"""
Seeder for lise (high school) placement data.
Loads pre-cleaned CSV files into the database using bulk inserts.
"""

import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.modules.lise.models import (
    Lise,
    LisePlacement,
    LisePlacement2025,
    ScoreRankingDistribution,
)


DATA_DIR = Path(__file__).parent.parent / "data"
LISE_DIR_2022_2024 = DATA_DIR / "lise" / "2022-2024"
LISE_DIR_2025 = DATA_DIR / "lise" / "2025"
SCORES_DIR = DATA_DIR / "scores"

BATCH_SIZE = 10000


def _val(value: str, dtype: str = "str") -> Any:
    """Convert CSV value to appropriate type."""
    if not value or value in ("", "nan", "None"):
        return None
    try:
        if dtype == "int":
            return int(float(value))
        elif dtype == "float":
            return float(value)
        elif dtype == "bool":
            return value.lower() == "true"
        return value.strip()
    except (ValueError, AttributeError):
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


def seed_lise_mapping(db: Session) -> int:
    """Seed lise master data from lise_mapping.csv files."""
    # Clear existing data first
    db.query(Lise).delete()
    db.commit()
    
    records = []
    
    # 2022-2024 mapping
    for row in _load_csv(LISE_DIR_2022_2024 / "lise_mapping.csv"):
        lise_id = _val(row.get("lise_id", ""), "int")
        if lise_id is None:
            continue
        records.append({
            "lise_id": lise_id,
            "lise_adi": _val(row.get("lise_adi", "")),
            "sehir": _val(row.get("sehir", "")),
            "year_group": "2022-2024",
        })
    
    # 2025 mapping (use canonical if exists)
    mapping_file = LISE_DIR_2025 / "lise_mapping_canonical.csv"
    if not mapping_file.exists():
        mapping_file = LISE_DIR_2025 / "lise_mapping.csv"
    
    for row in _load_csv(mapping_file):
        lise_id = _val(row.get("lise_id", ""), "int")
        if lise_id is None:
            continue
        records.append({
            "lise_id": lise_id,
            "lise_adi": _val(row.get("lise_adi", "")),
            "sehir": _val(row.get("sehir", "")),
            "year_group": "2025",
        })
    
    _bulk_insert(db, Lise, records)
    print(f"Seeded {len(records)} lise records")
    return len(records)


def seed_lise_placements(db: Session) -> int:
    """Seed lise placements from by_university folders."""
    # Clear existing data first
    db.query(LisePlacement).delete()
    db.commit()
    
    total = 0
    records = []
    commit_threshold = 50000  # Commit every 50k records for better performance
    
    for year_dir, year_group in [(LISE_DIR_2022_2024, "2022-2024"), (LISE_DIR_2025, "2025")]:
        by_uni_dir = year_dir / "by_university"
        if not by_uni_dir.exists():
            continue
        
        csv_files = sorted([f for f in by_uni_dir.glob("*.csv") if not f.name.startswith("_")])
        print(f"Processing {len(csv_files)} universities for {year_group}...")
        
        for i, csv_file in enumerate(csv_files, 1):
            university_slug = csv_file.stem
            uni_count = 0
            
            for row in _load_csv(csv_file):
                yop_kodu = _val(row.get("yop_kodu", ""))
                year = _val(row.get("year", ""), "int")
                lise_id = _val(row.get("lise_id", ""), "int")
                yerlesen_sayisi = _val(row.get("yerlesen_sayisi", ""), "int")
                
                if not all([yop_kodu, year, lise_id is not None, yerlesen_sayisi]):
                    continue
                
                records.append({
                    "university_slug": university_slug,
                    "yop_kodu": yop_kodu,
                    "year": year,
                    "lise_id": lise_id,
                    "yerlesen_sayisi": yerlesen_sayisi,
                    "school_type": _val(row.get("school_type", ""), "int"),
                })
                uni_count += 1
                
                if len(records) >= commit_threshold:
                    db.bulk_insert_mappings(LisePlacement, records)
                    db.commit()
                    total += len(records)
                    print(f"  Committed {total:,} records so far...")
                    records = []
            
            if i % 20 == 0 or i == len(csv_files):
                print(f"  [{year_group}] {i}/{len(csv_files)} universities processed")
    
    # Final batch
    if records:
        db.bulk_insert_mappings(LisePlacement, records)
        db.commit()
        total += len(records)
    
    print(f"Seeded {total:,} lise placements")
    return total


def seed_lise_placements_2025(db: Session) -> int:
    """Seed 2025 selected universities lise placements with detailed fields."""
    # Clear existing data first
    db.query(LisePlacement2025).delete()
    db.commit()
    
    records = []
    selected_dir = LISE_DIR_2025 / "selected_universities"
    
    if not selected_dir.exists():
        print("Warning: selected_universities directory not found")
        return 0
    
    # Map filename to source university
    source_map = {
        "fsm_lise_bazinda_yerlesen.csv": "fsm",
        "halic_lise_bazinda_yerlesen.csv": "halic",
        "ibnhaldun_lise_bazinda_yerlesen.csv": "ibnhaldun",
        "izu_lise_bazinda_yerlesen.csv": "izu",
        "mayis_lise_bazinda_yerlesen.csv": "mayis",
    }
    
    for csv_file in selected_dir.glob("*.csv"):
        source_uni = source_map.get(csv_file.name)
        if not source_uni:
            continue
        
        for row in _load_csv(csv_file):
            yop_kodu = _val(row.get("yop_kodu", ""))
            yerlesen_sayisi = _val(row.get("yerlesen_sayisi", ""), "int")
            
            if not yop_kodu or not yerlesen_sayisi:
                continue
            
            records.append({
                "source_university": source_uni,
                "yop_kodu": yop_kodu,
                "year": _val(row.get("year", ""), "int") or 2025,
                "lise_adi": _val(row.get("lise_adi", "")),
                "sehir": _val(row.get("sehir", "")),
                "ilce": _val(row.get("ilce", "")),
                "yerlesen_sayisi": yerlesen_sayisi,
                "is_ozel": _val(row.get("is_ozel", ""), "bool") or False,
                "is_fen": _val(row.get("is_fen", ""), "bool") or False,
                "is_anadolu": _val(row.get("is_anadolu", ""), "bool") or False,
                "is_acik_ogretim": _val(row.get("is_acik_ogretim", ""), "bool") or False,
            })
            
            if len(records) >= BATCH_SIZE:
                _bulk_insert(db, LisePlacement2025, records)
                records = []
    
    if records:
        _bulk_insert(db, LisePlacement2025, records)
    
    total = db.query(LisePlacement2025).count()
    print(f"Seeded {total} lise placements 2025 (selected universities)")
    return total


def seed_score_ranking_distribution(db: Session) -> int:
    """Seed score ranking distribution from JSON file."""
    # Clear existing data first
    db.query(ScoreRankingDistribution).delete()
    db.commit()
    
    json_path = SCORES_DIR / "score_ranking_distribution.json"

    if not json_path.exists():
        print(f"Warning: {json_path} not found")
        return 0
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    records = []
    
    for puan_turu, puan_data in data.items():
        # The distribution is nested inside with minScore, maxScore, and distribution list
        distribution = puan_data.get("distribution", [])
        for entry in distribution:
            puan = entry.get("score")
            siralama = entry.get("avgRanking")
            
            if puan is None or siralama is None:
                continue
            
            records.append({
                "puan_turu": puan_turu,
                "puan": float(puan),
                "siralama": int(siralama),
            })
    
    _bulk_insert(db, ScoreRankingDistribution, records)
    print(f"Seeded {len(records)} score ranking distributions")
    return len(records)


def clear_lise_data(db: Session):
    """Clear all lise-related tables."""
    db.query(ScoreRankingDistribution).delete()
    db.query(LisePlacement2025).delete()
    db.query(LisePlacement).delete()
    db.query(Lise).delete()
    db.commit()
    print("Cleared all lise data")


def seed_all_lise_data(db: Session):
    """Seed all lise data from CSV files."""
    # Each seed function clears its own table, no need for separate clear
    total = 0
    total += seed_lise_mapping(db)
    total += seed_lise_placements(db)
    total += seed_lise_placements_2025(db)
    total += seed_score_ranking_distribution(db)
    
    print(f"Total lise records seeded: {total}")
    return total


if __name__ == "__main__":
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        seed_all_lise_data(db)
    finally:
        db.close()
