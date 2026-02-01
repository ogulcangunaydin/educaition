from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings, Environment
from app import models, security
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Seeder: 
    def __init__(self, db: Session):
        self.db = db
    
    def run(self):
        """This error will raise if you forget to implement run method in subclass"""
        raise NotImplementedError


class UserSeeder(Seeder):
    SEED_USERS = {
        Environment.DEVELOPMENT: [
          {
              "username": "admin",
              "email": "admin@localhost.dev",
              "password": "DevAdmin@123!",
              "is_active": True,
          },
          {
              "username": "testuser",
              "email": "test@localhost.dev",
              "password": "TestUser@123!",
              "is_active": True,
          },
        ],
        Environment.STAGING: [
          {
              "username": "staging_admin",
              "email": "admin@staging.example.com",
              "password": "StagingAdmin@123!",
              "is_active": True,
          },
        ],
        Environment.PRODUCTION: [
          # Users should be created via admin panel or migration scripts
        ],
    }
    
    def run(self):
        users_to_create = self.SEED_USERS.get(settings.APP_ENV, [])
        
        if not users_to_create:
            logger.info(f"No seed users defined for {settings.APP_ENV.value} environment")
            return
        
        for user_data in users_to_create:
            self._create_user_if_not_exists(user_data)
    
    def _create_user_if_not_exists(self, user_data: dict):
        existing = self.db.query(models.User).filter(
            (models.User.username == user_data["username"]) |
            (models.User.email == user_data["email"])
        ).first()
        
        if existing:
            logger.info(f"User '{user_data['username']}' already exists, skipping")
            return
        
        hashed_password = security.get_password_hash(
            user_data["password"], 
            validate=False # Skip validation for controlled seed passwords
        )
        
        user = models.User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            is_active=user_data.get("is_active", True),
        )
        
        self.db.add(user)
        self.db.commit()
        
        logger.info(f"Created user '{user_data['username']}' ({user_data['email']})")
        
        # Only show password in development
        if settings.is_development:
            logger.info(f"Password: {user_data['password']}")


SEEDERS: List[type] = [
    UserSeeder,
    # Add more seeders as needed:
    # RoleSeeder,
    # PermissionSeeder,
    # DefaultSettingsSeeder,
]


def run_seeds(seeders: List[type] = None):
    logger.info(f"Starting database seeding for {settings.APP_ENV.value} environment")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    db = SessionLocal()
    
    try:
        seeders_to_run = seeders or SEEDERS
        
        for seeder_class in seeders_to_run:
            logger.info(f"\nRunning {seeder_class.__name__}...")
            seeder = seeder_class(db)
            seeder.run()
        
        logger.info("\nDatabase seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"\nSeeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    """Allow running seeds directly: python -m app.seeds.seed"""
    run_seeds()
