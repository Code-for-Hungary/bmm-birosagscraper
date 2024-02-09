from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_path = Path(__file__).resolve().parent.parent / 'data' / 'birosag.db'
database_url = 'sqlite:////' + str(db_path)
engine = create_engine(database_url)

# a sessionmaker(), also in the same scope as the engine
Session = sessionmaker(engine)
