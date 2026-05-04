import asyncio
import time
import json
from datetime import datetime
from litellm import acompletion
from config import MODELS
from database.db import SessionLocal, BenchmarkResult

async def ask_model(model_name:str,model_id:str,question:str):
    start = time.time()
    try:
        response = await acompletion(model=model_id,messages=[{"role":"user","content":question}],max_tokens=500)
        latency=round((time.time()-start)*1000,2)
        return {"model_name":model_name,"answer":response.choices[0].message.content,"latency_ms":latency,"tokens_used":response.usage.total_tokens,"status":"success"}
    except Exception as e:
        return {
            "model_name":model_name,
            "answer":None,
            "latency_ms":None,
            "tokens_used":None,
            "status":f"error : {str(e)[:100]}"
        }
async def run_benchmark_task(task : dict):
    jobs=[ask_model(name,model_id,task["question"])
          for name,model_id in MODELS.items()
          ]
    results=await asyncio.gather(*jobs)

    db = SessionLocal()
    saved=[]
    for r in results:
        record = BenchmarkResult(
            task_id = task["id"],
            category = task["category"],
            question = task["question"],
            model_name=r["model_name"],
            answer =r["answer"],
            latency_ms = r["latency_ms"],
            tokens_used = r["tokens_used"],
            status = r["status"],
            run_at= datetime.utcnow()
        )
        db.add(record)
        saved.append(r)
    db.commit()
    db.close()
    return saved