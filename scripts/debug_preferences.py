"""Debug script to investigate missing frequency data for yop_kodu 201990874."""
import sys
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.modules.tercih_stats.models import TercihPreference, TercihStats
from app.modules.universities.models import Program, ProgramYearlyStats, University

db = SessionLocal()

YOP = "201990874"

# 1. Check the program itself
prog = db.query(Program).filter(Program.yop_kodu == YOP).first()
if prog:
    uni = db.query(University).filter(University.id == prog.university_id).first()
    print(f"Program: {prog.name} ({prog.yop_kodu})")
    print(f"  University: {uni.name if uni else 'N/A'}")
    print(f"  Scholarship: {prog.scholarship}")
    print(f"  Puan type: {prog.puan_type}")
else:
    print(f"Program {YOP} NOT FOUND")
    sys.exit(1)

# 2. Check yearly stats
stats = db.query(ProgramYearlyStats).filter(ProgramYearlyStats.program_id == prog.id).all()
print(f"\nYearly stats ({len(stats)} records):")
for s in stats:
    print(f"  year={s.year} kontenjan={s.kontenjan} yerlesen={s.yerlesen} "
          f"taban={s.taban_puan} tavan={s.tavan_puan} has_data={s.has_data}")

# 3. Check TercihPreference for this yop_kodu
prefs = db.query(TercihPreference).filter(TercihPreference.yop_kodu == YOP).all()
print(f"\nTercihPreference for {YOP}: {len(prefs)} records")
for p in prefs[:20]:
    print(f"  year={p.year} type={p.preference_type} item={p.preferred_item} "
          f"count={p.tercih_sayisi} source={p.source_university}")

# 4. Check what years exist in preferences for halic
years_all = db.query(TercihPreference.year).filter(
    TercihPreference.source_university == "halic"
).distinct().all()
print(f"\nAll years with halic preferences: {sorted([y[0] for y in years_all])}")

# 5. Check how many distinct yop_kodus have preferences for 2025
count_2025 = db.query(TercihPreference.yop_kodu).filter(
    TercihPreference.year == 2025,
    TercihPreference.source_university == "halic"
).distinct().count()
print(f"Distinct yop_kodus with halic preferences for 2025: {count_2025}")

count_2024 = db.query(TercihPreference.yop_kodu).filter(
    TercihPreference.year == 2024,
    TercihPreference.source_university == "halic"
).distinct().count()
print(f"Distinct yop_kodus with halic preferences for 2024: {count_2024}")

# 6. Check TercihStats table too
tercih_stats = db.query(TercihStats).filter(TercihStats.yop_kodu == YOP).all()
print(f"\nTercihStats for {YOP}: {len(tercih_stats)} records")
for t in tercih_stats[:5]:
    print(f"  year={t.year} source={t.source_university}")

# 7. Sample some halic 2025 preferences to see what's there
sample = db.query(TercihPreference).filter(
    TercihPreference.source_university == "halic",
    TercihPreference.year == 2025
).limit(10).all()
print(f"\nSample halic 2025 preferences:")
for p in sample:
    print(f"  yop={p.yop_kodu} type={p.preference_type} item={p.preferred_item} count={p.tercih_sayisi}")

db.close()
