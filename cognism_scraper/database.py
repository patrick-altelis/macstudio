"""Database models and operations for the Cognism scraper."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
import config

Base = declarative_base()


class Company(Base):
    """Company model."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    website = Column(String(255))
    industry = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    profiles = relationship("Profile", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(name='{self.name}')>"


class Profile(Base):
    """Profile model for storing contact information."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    job_title = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    direct_phone = Column(String(50))
    linkedin_url = Column(String(255))
    location = Column(String(255))
    department = Column(String(255))
    seniority = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    company = relationship("Company", back_populates="profiles")

    def __repr__(self):
        return f"<Profile(name='{self.first_name} {self.last_name}', company='{self.company.name}')>"


# Database engine and session
engine = create_engine(config.DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def get_or_create_company(db: Session, name: str):
    """Get a company by name or create it if it doesn't exist."""
    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def save_profile(db: Session, company_id: int, profile_data: dict):
    """Save a profile to the database."""
    profile = Profile(company_id=company_id, **profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile