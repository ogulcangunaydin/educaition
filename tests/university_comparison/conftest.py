"""
Shared fixtures for the university_comparison test suite.

Uses an in-memory SQLite database with pre-seeded universities,
programs, yearly stats, prices, and tercih preferences so that
every test starts from a known state.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.universities.models import Program, ProgramYearlyStats, University
from app.modules.tercih_stats.models import ProgramPrice, TercihPreference


# ── In-memory SQLite engine ────────────────────────────────────────

# Teach SQLite how to compile PostgreSQL-specific types (JSONB, etc.)
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"


@pytest.fixture(scope="session")
def engine():
    """Create a shared SQLite in-memory engine for the entire test session.

    Uses StaticPool + check_same_thread=False so the same connection
    can be reused across threads (needed by FastAPI's TestClient).
    """
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db(engine):
    """Provide a transactional DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ── Seed data helpers ──────────────────────────────────────────────

def _make_university(db: Session, *, name: str, city: str, uni_type: str) -> University:
    uni = University(name=name, city=city, university_type=uni_type)
    db.add(uni)
    db.flush()
    return uni


def _make_program(
    db: Session,
    *,
    university: University,
    yop_kodu: str,
    name: str,
    faculty: str = "Mühendislik Fakültesi",
    puan_type: str = "say",
    scholarship: str | None = None,
    detail: str | None = None,
) -> Program:
    prog = Program(
        yop_kodu=yop_kodu,
        university_id=university.id,
        faculty=faculty,
        name=name,
        detail=detail,
        scholarship=scholarship,
        puan_type=puan_type,
    )
    db.add(prog)
    db.flush()
    return prog


def _make_stats(
    db: Session,
    *,
    program: Program,
    year: int,
    kontenjan: int = 50,
    yerlesen: int = 50,
    taban_puan: str = "300,000",
    tavan_puan: str = "400,000",
    tavan_basari_sirasi: str = "50.000",
    taban_basari_sirasi: int = 100_000,
    has_data: bool = True,
) -> ProgramYearlyStats:
    stat = ProgramYearlyStats(
        program_id=program.id,
        year=year,
        kontenjan=kontenjan,
        yerlesen=yerlesen,
        taban_puan=taban_puan,
        tavan_puan=tavan_puan,
        tavan_basari_sirasi=tavan_basari_sirasi,
        taban_basari_sirasi=taban_basari_sirasi,
        has_data=has_data,
    )
    db.add(stat)
    db.flush()
    return stat


def _make_price(
    db: Session,
    *,
    yop_kodu: str,
    scholarship_pct: float = 0,
    is_english: bool = False,
    full_price_2024: float | None = 100_000,
    discounted_price_2024: float | None = 100_000,
    full_price_2025: float | None = 120_000,
    discounted_price_2025: float | None = 120_000,
) -> ProgramPrice:
    price = ProgramPrice(
        yop_kodu=yop_kodu,
        scholarship_pct=scholarship_pct,
        is_english=is_english,
        full_price_2024=full_price_2024,
        full_price_2025=full_price_2025,
        discounted_price_2024=discounted_price_2024,
        discounted_price_2025=discounted_price_2025,
    )
    db.add(price)
    db.flush()
    return price


def _make_preference(
    db: Session,
    *,
    source_university: str,
    yop_kodu: str,
    year: int,
    preference_type: str,
    preferred_item: str,
    tercih_sayisi: int,
    university_type: str | None = None,
) -> TercihPreference:
    pref = TercihPreference(
        source_university=source_university,
        yop_kodu=yop_kodu,
        year=year,
        preference_type=preference_type,
        preferred_item=preferred_item,
        tercih_sayisi=tercih_sayisi,
        university_type=university_type,
    )
    db.add(pref)
    db.flush()
    return pref


# ── Composite "world" fixture ─────────────────────────────────────

@pytest.fixture()
def seed_data(db):
    """
    Pre-populate the DB with a realistic mini-dataset:

    Universities:
      - HALİÇ ÜNİVERSİTESİ  (Vakıf, İstanbul)
      - İSTANBUL ÜNİVERSİTESİ (Devlet, İstanbul)
      - ANKARA ÜNİVERSİTESİ   (Devlet, Ankara)
      - BAŞKENT ÜNİVERSİTESİ   (Vakıf, Ankara)

    Programs (all SAY, year=2024 with data):
      - HALIC-CS   : Bilgisayar Müh. (Burslu)       tavan_bs=40k  tbs=80k  taban=350 tavan=400
      - HALIC-EE   : Elektrik-Elektronik Müh.        tavan_bs=60k  tbs=120k taban=280 tavan=330
      - IST-CS     : Bilgisayar Müh.                 tavan_bs=30k  tbs=70k  taban=370 tavan=420
      - ANK-CS     : Bilgisayar Müh.                 tavan_bs=35k  tbs=75k  taban=360 tavan=410
      - BASK-CS    : Bilgisayar Müh. (%50 İndirimli) tavan_bs=45k  tbs=90k  taban=340 tavan=390
      - BASK-EE    : Elektrik-Elektronik Müh. (Ücretli) tavan_bs=55k tbs=110k taban=290 tavan=340

    Preferences (source=halic, yop_kodu=HALIC-CS, year=2024):
      city:       İstanbul=50, Ankara=30, İzmir=10
      university: İSTANBUL ÜNİVERSİTESİ=40, ANKARA ÜNİVERSİTESİ=25,
                  HALİÇ ÜNİVERSİTESİ=35 (own - should be excluded in uni filter),
                  BAŞKENT ÜNİVERSİTESİ=15
      program:    Bilgisayar Mühendisliği=60, Elektrik-Elektronik Mühendisliği=20

    Prices: for HALIC-CS and BASK-CS
    """
    # Universities
    halic = _make_university(db, name="HALİÇ ÜNİVERSİTESİ", city="İstanbul", uni_type="Vakıf")
    ist = _make_university(db, name="İSTANBUL ÜNİVERSİTESİ", city="İstanbul", uni_type="Devlet")
    ank = _make_university(db, name="ANKARA ÜNİVERSİTESİ", city="Ankara", uni_type="Devlet")
    bask = _make_university(db, name="BAŞKENT ÜNİVERSİTESİ", city="Ankara", uni_type="Vakıf")

    # Programs
    halic_cs = _make_program(db, university=halic, yop_kodu="HALIC-CS", name="Bilgisayar Mühendisliği", scholarship="Burslu")
    halic_ee = _make_program(db, university=halic, yop_kodu="HALIC-EE", name="Elektrik-Elektronik Mühendisliği")
    ist_cs = _make_program(db, university=ist, yop_kodu="IST-CS", name="Bilgisayar Mühendisliği")
    ank_cs = _make_program(db, university=ank, yop_kodu="ANK-CS", name="Bilgisayar Mühendisliği")
    bask_cs = _make_program(db, university=bask, yop_kodu="BASK-CS", name="Bilgisayar Mühendisliği", scholarship="%50 İndirimli")
    bask_ee = _make_program(db, university=bask, yop_kodu="BASK-EE", name="Elektrik-Elektronik Mühendisliği")

    # Yearly stats (year=2024)
    # Rankings: lower tavan_bs = better, higher tbs = worse
    # Scores: lower taban = worse, higher tavan = better
    _make_stats(db, program=halic_cs, year=2024, kontenjan=50, yerlesen=50,
                taban_puan="350,000", tavan_puan="400,000",
                tavan_basari_sirasi="40.000", taban_basari_sirasi=80_000)

    _make_stats(db, program=halic_ee, year=2024, kontenjan=40, yerlesen=20,
                taban_puan="280,000", tavan_puan="330,000",
                tavan_basari_sirasi="60.000", taban_basari_sirasi=120_000)

    _make_stats(db, program=ist_cs, year=2024, kontenjan=80, yerlesen=80,
                taban_puan="370,000", tavan_puan="420,000",
                tavan_basari_sirasi="30.000", taban_basari_sirasi=70_000)

    _make_stats(db, program=ank_cs, year=2024, kontenjan=60, yerlesen=55,
                taban_puan="360,000", tavan_puan="410,000",
                tavan_basari_sirasi="35.000", taban_basari_sirasi=75_000)

    _make_stats(db, program=bask_cs, year=2024, kontenjan=30, yerlesen=30,
                taban_puan="340,000", tavan_puan="390,000",
                tavan_basari_sirasi="45.000", taban_basari_sirasi=90_000)

    _make_stats(db, program=bask_ee, year=2024, kontenjan=30, yerlesen=10,
                taban_puan="290,000", tavan_puan="340,000",
                tavan_basari_sirasi="55.000", taban_basari_sirasi=110_000)

    # Preferences for HALIC-CS
    for item, count in [("İstanbul", 50), ("Ankara", 30), ("İzmir", 10)]:
        _make_preference(db, source_university="halic", yop_kodu="HALIC-CS",
                         year=2024, preference_type="city",
                         preferred_item=item, tercih_sayisi=count)

    for item, count in [
        ("İSTANBUL ÜNİVERSİTESİ", 40),
        ("HALİÇ ÜNİVERSİTESİ", 35),
        ("ANKARA ÜNİVERSİTESİ", 25),
        ("BAŞKENT ÜNİVERSİTESİ", 15),
    ]:
        _make_preference(db, source_university="halic", yop_kodu="HALIC-CS",
                         year=2024, preference_type="university",
                         preferred_item=item, tercih_sayisi=count)

    for item, count in [
        ("Bilgisayar Mühendisliği", 60),
        ("Elektrik-Elektronik Mühendisliği", 20),
    ]:
        _make_preference(db, source_university="halic", yop_kodu="HALIC-CS",
                         year=2024, preference_type="program",
                         preferred_item=item, tercih_sayisi=count)

    # Prices
    _make_price(db, yop_kodu="HALIC-CS", scholarship_pct=100,
                full_price_2024=150_000, discounted_price_2024=0,
                full_price_2025=180_000, discounted_price_2025=0)
    _make_price(db, yop_kodu="BASK-CS", scholarship_pct=50,
                full_price_2024=200_000, discounted_price_2024=100_000,
                full_price_2025=240_000, discounted_price_2025=120_000)

    db.flush()

    return {
        "universities": {"halic": halic, "ist": ist, "ank": ank, "bask": bask},
        "programs": {
            "halic_cs": halic_cs,
            "halic_ee": halic_ee,
            "ist_cs": ist_cs,
            "ank_cs": ank_cs,
            "bask_cs": bask_cs,
            "bask_ee": bask_ee,
        },
    }


# ── Service fixture ────────────────────────────────────────────────

@pytest.fixture()
def svc(db, seed_data):
    """Pre-seeded UniversityComparisonService ready to use."""
    from app.modules.university_comparison.service import UniversityComparisonService
    return UniversityComparisonService(db)


# ── Default compare request factory ───────────────────────────────

@pytest.fixture()
def make_request():
    """Factory for CompareRequest with sensible defaults pointing at HALIC-CS."""
    from app.modules.university_comparison.schemas import CompareRequest

    def _make(**overrides):
        defaults = dict(
            yop_kodu="HALIC-CS",
            year="2024",
            metric="ranking",
            university_type="all",
            source_university="halic",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
            record_limit=200,
            sort_by="spread",
        )
        defaults.update(overrides)
        return CompareRequest(**defaults)

    return _make
