from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database connection URL (modify with your actual username, password, and database name)
URL_DATABASE = 'mysql+pymysql://root:Abdullah_15@localhost:3306/WebScraperApp'

# SQLAlchemy engine
engine = create_engine(URL_DATABASE)

# SessionLocal class, used for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()