from fastapi import  FastAPI
from database.db import create_tables
from routers.benchmark import router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app=FastAPI(title="THARASU",version="1.0")

@app.on_event("startup")

def startup():
    create_tables()
    print("Database ready")

@app.get("/")
def root():
    return {"status" : "THARASU is running"}

app.include_router(router)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/index.html")