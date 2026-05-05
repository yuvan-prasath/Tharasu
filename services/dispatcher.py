import asyncio
import time
import json
from datetime import datetime
from litellm import acompletion
from scoring.engine import calculate_accuracy,calculate_tharasu_score, calculate_bleu
from scoring.judge import judge_answer
from config import MODELS, JUDGE_MODEL
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
    successful=[r for r in results if r["status"]=="success"]
    all_latencies=[r["latency_ms"] for r in successful if r["latency_ms"]]
    all_tokens=[r["tokens_used"] for r in successful if r["tokens_used"]]
    judge_model_name=None
    for name,model_id in MODELS.items():
        if model_id==JUDGE_MODEL:
            judge_model_name=name
            break
    enriched=[]
    for r in results:
        if r["status"]!="success" or not r["answer"]:
            r["judge_score"]=None
            r["judge_reason"]=None
        elif r["model_name"]==judge_model_name:
            r["judge_score"]=None
            r["judge_reason"]="Self- Evaluation Skipped"
        else:
            verdict = await judge_answer(task["question"],r["answer"])
            r["judge_score"]=verdict["score"]
            r["judge_reason"]=verdict["reason"]
        enriched.append(r)
    expected = task.get("expected_answer")
    reference = task.get("reference_answer")

    for r in enriched:
            r["accuracy"]=calculate_accuracy(r["answer"],expected) if expected else None
            r["bleu_score"] = calculate_bleu(r["answer"], expected) if expected else None

    for r in enriched:
            r["tharasu_score"]= calculate_tharasu_score(accuracy=r["accuracy"],judge_score=r["judge_score"],latency_ms=r["latency_ms"],tokens_used=r["tokens_used"],bleu_score=r["bleu_score"],all_latencies=all_latencies,all_tokens=all_tokens)

    db = SessionLocal()
    for r in enriched:
        record = BenchmarkResult(
            task_id = task["id"],
            category = task["category"],
            question = task["question"],
            model_name=r["model_name"],
            answer =r["answer"],
            latency_ms = r["latency_ms"],
            tokens_used = r["tokens_used"],
            status = r["status"],
            run_at= datetime.utcnow(),
            accuracy=r.get("accuracy"),
            bleu_score=r.get("bleu_score"),
            tharasu_score=r.get("tharasu_score"),
            judge_score=r.get("judge_score"),
            judge_reason=r.get("judge_reason"),
        )
        db.add(record)

    db.commit()
    db.close()
    return enriched