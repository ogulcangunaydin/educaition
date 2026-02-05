"""
Script to clean tercih CSV files for simpler seeding.

Cleaning operations:
1. Remove .0 suffix from yop_kodu columns
2. Convert Turkish number format (comma as decimal) to standard format
3. Convert empty/nan values to empty strings
"""

import csv
import os
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "app" / "data"
TERCIH_DIR_2022_2024 = DATA_DIR / "tercih" / "2022-2024"
TERCIH_DIR_2025 = DATA_DIR / "tercih" / "2025"
PRICES_DIR = DATA_DIR / "prices" / "2024-2025"


def clean_yop_kodu(value: str) -> str:
    """Remove .0 suffix from yop_kodu."""
    if not value:
        return ""
    return value.split(".")[0]


def clean_turkish_number(value: str) -> str:
    """Convert Turkish number format to standard format."""
    if not value or value.strip() in ("", "nan", "None", "NaN"):
        return ""
    # Handle Turkish format: "6,0" -> "6.0"
    value = value.strip().replace(".", "").replace(",", ".")
    try:
        return str(float(value))
    except ValueError:
        return ""


def clean_float(value: str) -> str:
    """Clean float value."""
    if not value or value.strip() in ("", "nan", "None", "NaN"):
        return ""
    try:
        return str(float(value.strip()))
    except ValueError:
        return ""


def clean_int(value: str) -> str:
    """Clean integer value."""
    if not value or value.strip() in ("", "nan", "None", "NaN"):
        return ""
    try:
        return str(int(float(value.strip())))
    except ValueError:
        return ""


def clean_csv_file(input_path: Path, output_path: Path, column_cleaners: dict):
    """Clean a CSV file with specified column cleaners."""
    if not input_path.exists():
        print(f"  Skipping (not found): {input_path}")
        return
    
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            cleaned_row = {}
            for col, value in row.items():
                if col in column_cleaners:
                    cleaned_row[col] = column_cleaners[col](value)
                else:
                    # Default: just strip whitespace
                    cleaned_row[col] = value.strip() if value else ""
            rows.append(cleaned_row)
    
    # Write cleaned file
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  Cleaned: {output_path.name} ({len(rows)} rows)")


def clean_combined_stats(tercih_dir: Path):
    """Clean combined_stats.csv file."""
    input_path = tercih_dir / "combined_stats.csv"
    output_path = input_path  # Overwrite
    
    cleaners = {
        "yop_kodu": clean_yop_kodu,
        "year": clean_int,
        "ortalama_tercih_edilme_sirasi_A": clean_float,
        "ortalama_yerlesen_tercih_sirasi_B": clean_float,
        "marka_etkinlik_degeri_A_div_B": clean_float,
    }
    
    clean_csv_file(input_path, output_path, cleaners)


def clean_istatistikleri(tercih_dir: Path, year_suffix: str):
    """Clean istatistikleri.csv file."""
    input_path = tercih_dir / "istatistikleri.csv"
    output_path = input_path  # Overwrite
    
    # Build cleaners based on year columns
    cleaners = {"yop_kodu": clean_yop_kodu}
    
    if year_suffix == "2022-2024":
        for year in ["2022", "2023", "2024"]:
            cleaners[f"bir_kontenjana_talip_olan_aday_sayisi_{year}"] = clean_turkish_number
            cleaners[f"ilk_uc_sirada_tercih_eden_sayisi_{year}"] = clean_float
            cleaners[f"ilk_uc_sirada_tercih_eden_orani_{year}"] = clean_turkish_number
            cleaners[f"ilk_uc_tercih_olarak_yerlesen_sayisi_{year}"] = clean_float
            cleaners[f"ilk_uc_tercih_olarak_yerlesen_orani_{year}"] = clean_turkish_number
    else:
        cleaners["bir_kontenjana_talip_olan_aday_sayisi_2025"] = clean_turkish_number
        cleaners["ilk_uc_sirada_tercih_eden_sayisi_2025"] = clean_float
        cleaners["ilk_uc_sirada_tercih_eden_orani_2025"] = clean_turkish_number
        cleaners["ilk_uc_tercih_olarak_yerlesen_sayisi_2025"] = clean_float
        cleaners["ilk_uc_tercih_olarak_yerlesen_orani_2025"] = clean_turkish_number
    
    clean_csv_file(input_path, output_path, cleaners)


def clean_preferences(tercih_dir: Path):
    """Clean preference files."""
    prefs_dir = tercih_dir / "preferences"
    if not prefs_dir.exists():
        return
    
    for pref_file in ["selected_universities_iller.csv", 
                      "selected_universities_universiteler.csv",
                      "selected_universities_programlar.csv"]:
        input_path = prefs_dir / pref_file
        if not input_path.exists():
            continue
        
        cleaners = {
            "yop_kodu": clean_yop_kodu,
            "year": clean_int,
            "tercih_sayisi": clean_int,
        }
        
        clean_csv_file(input_path, input_path, cleaners)


def clean_prices():
    """Clean prices_processed.csv file."""
    input_path = PRICES_DIR / "prices_processed.csv"
    output_path = input_path  # Overwrite
    
    cleaners = {
        "yop_kodu": clean_yop_kodu,
        "scholarship_pct": clean_float,
        "full_price_2024": clean_float,
        "full_price_2025": clean_float,
        "discounted_price_2024": clean_float,
        "discounted_price_2025": clean_float,
    }
    
    clean_csv_file(input_path, output_path, cleaners)


def main():
    print("Cleaning tercih CSV files...")
    
    print("\n=== Cleaning prices ===")
    clean_prices()
    
    print("\n=== Cleaning 2022-2024 tercih data ===")
    clean_combined_stats(TERCIH_DIR_2022_2024)
    clean_istatistikleri(TERCIH_DIR_2022_2024, "2022-2024")
    clean_preferences(TERCIH_DIR_2022_2024)
    
    print("\n=== Cleaning 2025 tercih data ===")
    clean_combined_stats(TERCIH_DIR_2025)
    clean_istatistikleri(TERCIH_DIR_2025, "2025")
    clean_preferences(TERCIH_DIR_2025)
    
    print("\n✅ All CSV files cleaned!")


if __name__ == "__main__":
    main()
