"""
Shared fixtures for the tercih_stats batch endpoint tests.

Uses an in-memory SQLite database with pre-seeded TercihStats,
TercihIstatistikleri (detailed stats), and ProgramPrice records.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.tercih_stats.models import (
    ProgramPrice,
    TercihIstatistikleri,
    TercihStats,
)
from app.modules.universities.models import Program, ProgramYearlyStats, University

# Teach SQLite how to compile PostgreSQL-specific types (JSONB, etc.)
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def seed_data(db):
    """
    Pre-populate the DB with tercih stats test data.

    Programs (via universities):
      - PROG-A  (yop_kodu="100001")
      - PROG-B  (yop_kodu="100002")
      - PROG-C  (yop_kodu="100003")

    TercihStats:
      - 100001, year=2024: tercih_edilme=5.0, yerlesen_tercih=3.0, marka=1.67
      - 100001, year=2023: tercih_edilme=6.0, yerlesen_tercih=4.0, marka=1.50
      - 100002, year=2024: tercih_edilme=8.0, yerlesen_tercih=7.0, marka=1.14
      - 100003, year=2024: tercih_edilme=3.0, yerlesen_tercih=2.0, marka=1.50

    TercihIstatistikleri:
      - 100001: all years populated
      - 100002: only 2024 populated

    ProgramPrices:
      - 100001: scholarship=100, prices set
      - 100002: scholarship=0, prices set
    """
    # University
    uni = University(name="TEST ÜNİVERSİTESİ", city="İstanbul", university_type="Vakıf")
    db.add(uni)
    db.flush()

    # Programs
    for yop, name in [
        ("100001", "Program A"),
        ("100002", "Program B"),
        ("100003", "Program C"),
    ]:
        prog = Program(
            yop_kodu=yop,
            university_id=uni.id,
            faculty="Test Fakültesi",
            name=name,
            puan_type="say",
        )
        db.add(prog)
    db.flush()

    # TercihStats
    stats_data = [
        ("100001", 2024, 5.0, 3.0, 1.67),
        ("100001", 2023, 6.0, 4.0, 1.50),
        ("100002", 2024, 8.0, 7.0, 1.14),
        ("100003", 2024, 3.0, 2.0, 1.50),
    ]
    for yop, year, tercih, yerlesen, marka in stats_data:
        db.add(TercihStats(
            yop_kodu=yop,
            year=year,
            ortalama_tercih_edilme_sirasi=tercih,
            ortalama_yerlesen_tercih_sirasi=yerlesen,
            marka_etkinlik_degeri=marka,
        ))

    # TercihIstatistikleri
    db.add(TercihIstatistikleri(
        yop_kodu="100001",
        bir_kontenjana_talip_olan_aday_sayisi_2024=12.5,
        ilk_uc_sirada_tercih_eden_sayisi_2024=80,
        ilk_uc_sirada_tercih_eden_orani_2024=40.0,
        ilk_uc_tercih_olarak_yerlesen_sayisi_2024=30,
        ilk_uc_tercih_olarak_yerlesen_orani_2024=60.0,
        bir_kontenjana_talip_olan_aday_sayisi_2023=10.0,
    ))
    db.add(TercihIstatistikleri(
        yop_kodu="100002",
        bir_kontenjana_talip_olan_aday_sayisi_2024=8.0,
        ilk_uc_sirada_tercih_eden_sayisi_2024=40,
        ilk_uc_sirada_tercih_eden_orani_2024=20.0,
    ))

    # ProgramPrices
    db.add(ProgramPrice(
        yop_kodu="100001",
        scholarship_pct=100,
        is_english=False,
        full_price_2024=150_000,
        discounted_price_2024=0,
        full_price_2025=180_000,
        discounted_price_2025=0,
    ))
    db.add(ProgramPrice(
        yop_kodu="100002",
        scholarship_pct=0,
        is_english=False,
        full_price_2024=200_000,
        discounted_price_2024=200_000,
        full_price_2025=240_000,
        discounted_price_2025=240_000,
    ))

    db.flush()
    return {
        "yop_kodlari": ["100001", "100002", "100003"],
    }
