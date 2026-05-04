from fastapi import  FastAPI
from database.db import create_tables
from routers.benchmark import router

app=FastAPI(title="THARASU",version="1.0")

@app.on_event("startup")

def startup():
    create_tables()
    print("Database ready")

@app.get("/")
def root():
    return {"status" : "THARASU is running"}

app.include_router(router)