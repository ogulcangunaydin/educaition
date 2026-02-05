"""
Seeder for tercih statistics data.
Loads data from CSV files into the database.

File locations:
- prices/2024-2025/prices_processed.csv
- tercih/2022-2024/ (historical data)
  - combined_stats.csv
  - istatistikleri.csv
  - kullanma_oranlari.csv
  - preferences/selected_universities_*.csv
- tercih/2025/ (current year data)
  - combined_stats.csv
  - istatistikleri.csv
  - kullanma_oranlari.csv
  - preferences/selected_universities_*.csv
"""

import csv
from pathlib import Path
from typing import Optional

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


def parse_turkish_number(value: str) -> Optional[float]:
    """Parse Turkish number format (comma as decimal separator)."""
    if not value or value.strip() in ("", "nan", "None"):
        return None
    
    # Handle Turkish format: "6,0" -> 6.0
    value = value.strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def parse_float(value: str) -> Optional[float]:
    """Parse a float value, returning None for empty/invalid values."""
    if not value or value.strip() in ("", "nan", "None"):
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def parse_int(value: str) -> Optional[int]:
    """Parse an integer value, returning None for empty/invalid values."""
    if not value or value.strip() in ("", "nan", "None"):
        return None
    try:
        # Handle float strings like "101710027.0"
        return int(float(value.strip()))
    except ValueError:
        return None


def seed_program_prices(db: Session) -> int:
    """Seed program prices from prices/2024-2025/prices_processed.csv."""
    csv_path = PRICES_DIR / "prices_processed.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found, skipping program prices")
        return 0
    
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yop_kodu = row.get("yop_kodu", "").split(".")[0]  # Remove decimal
            if not yop_kodu:
                continue
            
            price = ProgramPrice(
                yop_kodu=yop_kodu,
                is_english=row.get("is_english", "").lower() == "true",
                scholarship_pct=parse_float(row.get("scholarship_pct", "")),
                full_price_2024=parse_float(row.get("full_price_2024", "")),
                full_price_2025=parse_float(row.get("full_price_2025", "")),
                discounted_price_2024=parse_float(row.get("discounted_price_2024", "")),
                discounted_price_2025=parse_float(row.get("discounted_price_2025", "")),
            )
            db.add(price)
            count += 1
            
            if count % 1000 == 0:
                db.flush()
    
    db.commit()
    print(f"Seeded {count} program prices")
    return count


def _seed_tercih_stats_from_file(db: Session, csv_path: Path) -> int:
    """Seed tercih stats from a combined_stats.csv file."""
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found, skipping")
        return 0
    
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yop_kodu = row.get("yop_kodu", "").split(".")[0]
            year = parse_int(row.get("year", ""))
            if not yop_kodu or not year:
                continue
            
            stat = TercihStats(
                yop_kodu=yop_kodu,
                year=year,
                ortalama_tercih_edilme_sirasi=parse_float(row.get("ortalama_tercih_edilme_sirasi_A", "")),
                ortalama_yerlesen_tercih_sirasi=parse_float(row.get("ortalama_yerlesen_tercih_sirasi_B", "")),
                marka_etkinlik_degeri=parse_float(row.get("marka_etkinlik_degeri_A_div_B", "")),
            )
            db.add(stat)
            count += 1
            
            if count % 1000 == 0:
                db.flush()
    
    return count


def seed_tercih_stats(db: Session) -> int:
    """Seed tercih stats from all year folders."""
    count = 0
    
    # Seed 2022-2024 data
    count += _seed_tercih_stats_from_file(db, TERCIH_DIR_2022_2024 / "combined_stats.csv")
    
    # Seed 2025 data
    count += _seed_tercih_stats_from_file(db, TERCIH_DIR_2025 / "combined_stats.csv")
    
    db.commit()
    print(f"Seeded {count} tercih stats")
    return count


def seed_tercih_istatistikleri(db: Session) -> int:
    """Seed detailed tercih istatistikleri from both year folders."""
    count = 0
    
    # First, seed from 2022-2024 file
    csv_path_2022_2024 = TERCIH_DIR_2022_2024 / "istatistikleri.csv"
    if csv_path_2022_2024.exists():
        with open(csv_path_2022_2024, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yop_kodu = row.get("yop_kodu", "").split(".")[0]
                if not yop_kodu:
                    continue
                
                istat = TercihIstatistikleri(
                    yop_kodu=yop_kodu,
                    bir_kontenjana_talip_olan_aday_sayisi_2022=parse_turkish_number(
                        row.get("bir_kontenjana_talip_olan_aday_sayisi_2022", "")
                    ),
                    bir_kontenjana_talip_olan_aday_sayisi_2023=parse_turkish_number(
                        row.get("bir_kontenjana_talip_olan_aday_sayisi_2023", "")
                    ),
                    bir_kontenjana_talip_olan_aday_sayisi_2024=parse_turkish_number(
                        row.get("bir_kontenjana_talip_olan_aday_sayisi_2024", "")
                    ),
                    ilk_uc_sirada_tercih_eden_sayisi_2022=parse_float(
                        row.get("ilk_uc_sirada_tercih_eden_sayisi_2022", "")
                    ),
                    ilk_uc_sirada_tercih_eden_sayisi_2023=parse_float(
                        row.get("ilk_uc_sirada_tercih_eden_sayisi_2023", "")
                    ),
                    ilk_uc_sirada_tercih_eden_sayisi_2024=parse_float(
                        row.get("ilk_uc_sirada_tercih_eden_sayisi_2024", "")
                    ),
                    ilk_uc_sirada_tercih_eden_orani_2022=parse_turkish_number(
                        row.get("ilk_uc_sirada_tercih_eden_orani_2022", "")
                    ),
                    ilk_uc_sirada_tercih_eden_orani_2023=parse_turkish_number(
                        row.get("ilk_uc_sirada_tercih_eden_orani_2023", "")
                    ),
                    ilk_uc_sirada_tercih_eden_orani_2024=parse_turkish_number(
                        row.get("ilk_uc_sirada_tercih_eden_orani_2024", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_sayisi_2022=parse_float(
                        row.get("ilk_uc_tercih_olarak_yerlesen_sayisi_2022", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_sayisi_2023=parse_float(
                        row.get("ilk_uc_tercih_olarak_yerlesen_sayisi_2023", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_sayisi_2024=parse_float(
                        row.get("ilk_uc_tercih_olarak_yerlesen_sayisi_2024", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_orani_2022=parse_turkish_number(
                        row.get("ilk_uc_tercih_olarak_yerlesen_orani_2022", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_orani_2023=parse_turkish_number(
                        row.get("ilk_uc_tercih_olarak_yerlesen_orani_2023", "")
                    ),
                    ilk_uc_tercih_olarak_yerlesen_orani_2024=parse_turkish_number(
                        row.get("ilk_uc_tercih_olarak_yerlesen_orani_2024", "")
                    ),
                )
                db.add(istat)
                count += 1
                
                if count % 1000 == 0:
                    db.flush()
        
        db.commit()
    
    # Then, update with 2025 data
    csv_path_2025 = TERCIH_DIR_2025 / "istatistikleri.csv"
    if csv_path_2025.exists():
        updated_count = 0
        with open(csv_path_2025, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yop_kodu = row.get("yop_kodu", "").split(".")[0]
                if not yop_kodu:
                    continue
                
                # Try to find existing record
                istat = db.query(TercihIstatistikleri).filter_by(yop_kodu=yop_kodu).first()
                
                if istat:
                    # Update existing record with 2025 data
                    istat.bir_kontenjana_talip_olan_aday_sayisi_2025 = parse_turkish_number(
                        row.get("bir_kontenjana_talip_olan_aday_sayisi_2025", "")
                    )
                    istat.ilk_uc_sirada_tercih_eden_sayisi_2025 = parse_float(
                        row.get("ilk_uc_sirada_tercih_eden_sayisi_2025", "")
                    )
                    istat.ilk_uc_sirada_tercih_eden_orani_2025 = parse_turkish_number(
                        row.get("ilk_uc_sirada_tercih_eden_orani_2025", "")
                    )
                    istat.ilk_uc_tercih_olarak_yerlesen_sayisi_2025 = parse_float(
                        row.get("ilk_uc_tercih_olarak_yerlesen_sayisi_2025", "")
                    )
                    istat.ilk_uc_tercih_olarak_yerlesen_orani_2025 = parse_turkish_number(
                        row.get("ilk_uc_tercih_olarak_yerlesen_orani_2025", "")
                    )
                    updated_count += 1
                else:
                    # Create new record for 2025-only programs
                    istat = TercihIstatistikleri(
                        yop_kodu=yop_kodu,
                        bir_kontenjana_talip_olan_aday_sayisi_2025=parse_turkish_number(
                            row.get("bir_kontenjana_talip_olan_aday_sayisi_2025", "")
                        ),
                        ilk_uc_sirada_tercih_eden_sayisi_2025=parse_float(
                            row.get("ilk_uc_sirada_tercih_eden_sayisi_2025", "")
                        ),
                        ilk_uc_sirada_tercih_eden_orani_2025=parse_turkish_number(
                            row.get("ilk_uc_sirada_tercih_eden_orani_2025", "")
                        ),
                        ilk_uc_tercih_olarak_yerlesen_sayisi_2025=parse_float(
                            row.get("ilk_uc_tercih_olarak_yerlesen_sayisi_2025", "")
                        ),
                        ilk_uc_tercih_olarak_yerlesen_orani_2025=parse_turkish_number(
                            row.get("ilk_uc_tercih_olarak_yerlesen_orani_2025", "")
                        ),
                    )
                    db.add(istat)
                    count += 1
                
                if updated_count % 1000 == 0:
                    db.flush()
        
        db.commit()
        print(f"Updated {updated_count} tercih istatistikleri with 2025 data")
    
    print(f"Seeded {count} tercih istatistikleri total")
    return count


def _seed_preferences_from_dir(db: Session, preferences_dir: Path) -> int:
    """Seed tercih preferences from a preferences directory."""
    count = 0
    
    # Process city preferences from consolidated file
    cities_file = preferences_dir / "selected_universities_iller.csv"
    if cities_file.exists():
        count += _seed_consolidated_preference_file(db, cities_file, "city")
    
    # Process university preferences from consolidated file
    unis_file = preferences_dir / "selected_universities_universiteler.csv"
    if unis_file.exists():
        count += _seed_consolidated_preference_file(db, unis_file, "university")
    
    # Process program preferences from consolidated file
    progs_file = preferences_dir / "selected_universities_programlar.csv"
    if progs_file.exists():
        count += _seed_consolidated_preference_file(db, progs_file, "program")
    
    return count


def seed_tercih_preferences(db: Session) -> int:
    """Seed tercih preferences from all year folders."""
    count = 0
    
    # Seed from 2022-2024
    count += _seed_preferences_from_dir(db, TERCIH_DIR_2022_2024 / "preferences")
    
    # Seed from 2025
    count += _seed_preferences_from_dir(db, TERCIH_DIR_2025 / "preferences")
    
    db.commit()
    print(f"Seeded {count} tercih preferences")
    return count


def _seed_consolidated_preference_file(db: Session, csv_path: Path, pref_type: str) -> int:
    """Seed preferences from a consolidated CSV file with source_university column."""
    count = 0
    
    # Map column names based on preference type
    item_col = {
        "city": "il",
        "university": "universite",
        "program": "program",
    }[pref_type]
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_uni = row.get("source_university", "").strip()
            yop_kodu = row.get("yop_kodu", "").split(".")[0]
            year = parse_int(row.get("year", ""))
            preferred_item = row.get(item_col, "").strip()
            tercih_sayisi = parse_int(row.get("tercih_sayisi", ""))
            
            if not source_uni or not yop_kodu or not year or not preferred_item or not tercih_sayisi:
                continue
            
            pref = TercihPreference(
                source_university=source_uni,
                yop_kodu=yop_kodu,
                year=year,
                preference_type=pref_type,
                preferred_item=preferred_item,
                tercih_sayisi=tercih_sayisi,
                university_type=row.get("university_type", "").strip() if pref_type == "university" else None,
            )
            db.add(pref)
            count += 1
            
            if count % 2000 == 0:
                db.flush()
    
    return count


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
