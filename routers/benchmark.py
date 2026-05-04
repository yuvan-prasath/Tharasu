
from fastapi import APIRouter
from services.dispatcher import run_benchmark_task
from database.db import SessionLocal, BenchmarkResult
import json
router = APIRouter(prefix="/benchmark",tags=["Benchmark"])

@router.post("/run")
async def run_benchmark():
    with open("tasks/task_library.json") as f:
        tasks = json.load(f)
    all_results = []
    for task in tasks:
        results=await run_benchmark_task(task)
        all_results.extend(results)
    return {"message":f" Ran {len(tasks)} tasks across {len(all_results)} model responses"}

@router.get("/results")
def get_results():
    db = SessionLocal()
    results = db.query(BenchmarkResult).order_by(BenchmarkResult.id.desc()).limit(50).all()
    db.close()
    return [{
        "id": r.id,
        "task_id": r.task_id,
        "category":r.category,
        "model": r.model_name,
        "latency_ms":r.latency_ms,
        "tokens_used":r.tokens_used,
        "status":r.status,
        "run_at": str(r.run_at)

    }
    for r in results
    ]
@router.get("/leaderboard")
def get_leaderboard():
    db = SessionLocal()
    results = db.query(BenchmarkResult).filter(BenchmarkResult.status=="success").all()
    db.close()
    stats = {}
    for r in results:
        if r.model_name not in stats:
            stats[r.model_name]={"total":0,"latency_sum":0,"tokens_sum":0}
        stats[r.model_name]["total"]+=1
        stats[r.model_name]["latency_sum"]+=r.latency_ms or 0
        stats[r.model_name]["tokens_sum"]+=r.tokens_used or 0

    leaderboard = []
    for model,s in stats.items():
            leaderboard.append({
                "model":model,
                "tasks_completed":s["total"],
                "avg_latency_ms":round(s["latency_sum"]/s["total"],2),
                "avg_tokens":round(s["tokens_sum"]/s["total"],2),

            })
    return sorted(leaderboard,key=lambda x: x["avg_latency_ms"])