
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
    return {"message":f" Ran {len(tasks)} tasks across {len(all_results)} model responses",
            "total_responses":len(all_results)}

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
        "accuracy":r.accuracy,
        "blue_score":r.bleu_score,
        "judge_score":r.judge_score,
        "judge_reason":r.judge_reason,
        "run_at": str(r.run_at)
    }
    for r in results
    ]
@router.get("/leaderboard")
def get_leaderboard():
    db = SessionLocal()
    results = db.query(BenchmarkResult).filter(BenchmarkResult.status == "success").all()
    db.close()

    stats = {}
    for r in results:
        m = r.model_name
        if m not in stats:
            stats[m] = {
                "total": 0,
                "latency_sum": 0,
                "tokens_sum": 0,
                "tharasu_sum": 0,       # ← was missing
                "tharasu_count": 0,
                "judge_sum": 0,
                "judge_count": 0,
                "accuracy_sum": 0,
                "accuracy_count": 0,
                "bleu_sum": 0,
                "bleu_count": 0,
            }
        stats[m]["total"] += 1
        stats[m]["latency_sum"] += r.latency_ms or 0
        stats[m]["tokens_sum"] += r.tokens_used or 0

        if r.tharasu_score is not None:         # ← all inside the for loop
            stats[m]["tharasu_sum"] += r.tharasu_score
            stats[m]["tharasu_count"] += 1
        if r.judge_score is not None:
            stats[m]["judge_sum"] += r.judge_score
            stats[m]["judge_count"] += 1
        if r.accuracy is not None:
            stats[m]["accuracy_sum"] += r.accuracy
            stats[m]["accuracy_count"] += 1
        if r.bleu_score is not None:
            stats[m]["bleu_sum"] += r.bleu_score
            stats[m]["bleu_count"] += 1

    leaderboard = []
    for model, s in stats.items():
        leaderboard.append({
            "model": model,
            "tasks_completed": s["total"],
            "avg_latency_ms": round(s["latency_sum"] / s["total"], 2),
            "avg_tokens": round(s["tokens_sum"] / s["total"], 2),
            "avg_tharasu_score": round(s["tharasu_sum"] / s["tharasu_count"], 2) if s["tharasu_count"] else None,
            "avg_judge_score": round(s["judge_sum"] / s["judge_count"], 2) if s["judge_count"] else None,
            "avg_accuracy": round(s["accuracy_sum"] / s["accuracy_count"], 2) if s["accuracy_count"] else None,
            "avg_bleu": round(s["bleu_sum"] / s["bleu_count"], 4) if s["bleu_count"] else None,
        })

    return sorted(leaderboard, key=lambda x: x["avg_tharasu_score"] or 0, reverse=True)