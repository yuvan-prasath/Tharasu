import statistics
from database.db import SessionLocal, BenchmarkResult
from sqlalchemy import func

def calculate_consistency_for_task(task_id:str,model_name:str)-> float:
    db = SessionLocal()
    scores = db.query(BenchmarkResult.judge_score).filter(BenchmarkResult.task_id==task_id,BenchmarkResult.model_name,BenchmarkResult.judge_score!=None).all()
    db.close()
    scores= [s[0] for s in scores]
    if len(scores)<3:
        return None
    mean = statistics.mean(scores)
    std = statistics.stdev(scores)
    if mean==0:
        return 1.0

    consistency=1-(std/mean)
    return round(max(0.0,min(1.0,consistency)),4)

def get_all_consistency_scores()->dict:
    db = SessionLocal()
    results=db.query(BenchmarkResult.task_id,BenchmarkResult.model_name).distinct().all()
    db.close()

    output={}
    for task_id,model_name in results:
        score= calculate_consistency_for_task(task_id,model_name)
        if score is not None:
            key = f"{task_id}::{model_name}"
            output[key] = score
    return output
