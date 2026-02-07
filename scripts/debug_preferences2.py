"""Check program details for 5 programs missing city/uni preferences."""
import sys
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.modules.universities.models import Program, ProgramYearlyStats
from app.modules.tercih_stats.models import TercihPreference, ProgramPrice

db = SessionLocal()

missing = ["201990734", "201990874", "201990902", "201990923", "201990951"]
print("=== Programs missing city/university preferences ===\n")
for yop in missing:
    p = db.query(Program).filter(Program.yop_kodu == yop).first()
    if not p:
        print(f"{yop}: NOT FOUND")
        continue
    stats = db.query(ProgramYearlyStats).filter(
        ProgramYearlyStats.program_id == p.id, ProgramYearlyStats.year == 2025
    ).first()
    print(f"{yop}: {p.name} ({p.scholarship})")
    if stats:
        print(f"  2025: kontenjan={stats.kontenjan} yerlesen={stats.yerlesen}")
    
    prog_prefs = db.query(TercihPreference).filter(
        TercihPreference.yop_kodu == yop,
        TercihPreference.year == 2025,
        TercihPreference.preference_type == "program",
    ).count()
    print(f"  program prefs: {prog_prefs}")

# Now check: do programs with few enrolled students tend to be missing?
print("\n=== Programs WITH city prefs (sample of low-yerlesen) ===\n")
from sqlalchemy import func
# Get some halic programs that DO have city prefs and see their yerlesen
city_yops = db.query(TercihPreference.yop_kodu).filter(
    TercihPreference.source_university == "halic",
    TercihPreference.year == 2025,
    TercihPreference.preference_type == "city"
).distinct().subquery()

programs_with_city = (
    db.query(Program, ProgramYearlyStats)
    .join(ProgramYearlyStats, ProgramYearlyStats.program_id == Program.id)
    .filter(
        Program.yop_kodu.in_(db.query(city_yops)),
        ProgramYearlyStats.year == 2025,
    )
    .order_by(ProgramYearlyStats.yerlesen.asc())
    .limit(10)
    .all()
)

for prog, stat in programs_with_city:
    print(f"  {prog.yop_kodu}: {prog.name} ({prog.scholarship}) — yerlesen={stat.yerlesen}")

db.close()
