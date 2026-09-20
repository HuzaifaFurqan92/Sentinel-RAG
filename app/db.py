from typing import Optional,List
from sqlalchemy import create_engine
import os
from sqlalchemy.orm import sessionmaker,Session
from datetime import datetime

from .models import Base,Trace
from .schemas import TraceCreate,TraceRead

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}, 
        echo=False
    )
sessionlocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

#This is passed onto FastAPI and FastApi performes ops on this
#to interact with ou real db
def get_db():
    db = sessionlocal()
    try : 
        yield db
    finally: 
        db.close()

#?
def init_db():
   Base.metadata.create_all(bind=engine)
   
def create_trace(db : Session , trace_data: TraceCreate) -> Trace:
    db_trace = Trace(
        query = trace_data.query,
        response = trace_data.response,
        retrieved_context = trace_data.retrieved_context
    )
    db.add(db_trace)
    #Data stored at db but python doesnt know about id and created_at 
    #values as thats defined once data is in db
    db.commit()
    #we do db refresh to read these values sp python also knows it 
    db.refresh(db_trace)
    return db_trace

def get_trace(db:Session ,id : int) -> Trace:
    return db.query(Trace).filter(Trace.id == id).first()

def get_list_traces( db :Session , limit : int = 100 )-> List[Trace]:
    return db.query(Trace).order_by(Trace.created_at.desc()).limit(limit).all()    

    