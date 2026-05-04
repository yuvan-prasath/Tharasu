from sqlalchemy import create_engine, Column, String, Float, Integer,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///tharasu.db"

engine = create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal= sessionmaker(bind=engine)
Base=declarative_base()
class BenchmarkResult(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True,index=True)
    task_id = Column(String,index=True)
    category = Column(String)
    question = Column(String)
    model_name = Column(String)
    answer = Column(String)
    latency_ms = Column(Float)
    tokens_used = Column(Float)
    status = Column(String)
    run_at = Column(DateTime,default=datetime.utcnow)

def create_tables():
    Base.metadata.create_all(engine)
