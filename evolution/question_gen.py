import json
import re
from litellm import acompletion
from config import JUDGE_MODEL
from database.db import SessionLocal, BenchmarkResult

EVOLUTION_PROMPT = """You are an expert AI benchmark designer.

The following category had poor performance across all models: {category}

Failed tasks:
{failed_tasks}

Generate 5 NEW benchmark questions that are HARDER than the ones above.
Each question must test the same category but require deeper reasoning.

Return ONLY a valid JSON array. No markdown, no explanation.
Format:
[
  {{
    "id": "{category}_evo_{index}",
    "category": "{category}",
    "question": "<your harder question>",
    "expected_answer": "<short correct answer or null>",
    "reference_answer": "<detailed reference answer>"
  }}
]"""

async def generate_harder_questions(category:str, failed_tasks:list) -> list:
    failed_text= "\n".join([f"-{t['question']}" for t in failed_tasks[:5]])
    prompt=EVOLUTION_PROMPT.format(category=category,failed_tasks=failed_text,index={"index"})
    try :
        response = await acompletion(model=JUDGE_MODEL,messages=[{'role':"user","content": prompt}],max_tokens=1000,temperature=0.7)
        raw = response.choices[0].message.content.strip()
        raw=re.sub(r"```json|```", "", raw).strip()
        questions = json.loads(raw)
        for i,q in enumerate(questions):
            q["id"]=f"{category}_evo_{i+1:03d}"
        return questions
    except Exception as e:
        print(f"Evolution error for {category} : {e}")
        return []

def get_failed_categories(threshold:float=5.0)->dict:
    db = SessionLocal()
    results=db.query(BenchmarkResult).filter(BenchmarkResult.status=="success").all()
    db.close()

    task_groups={}
    for r in  results:
        if r.task_id not in task_groups:
            task_groups[r.task_id]={
                "category" : r.category,
                "question" : r.question,
                "scores" : []
            }
        if r.judge_score is not None:
            task_groups[r.task_id]["scores"].append(r.judge_score)

        failed_by_category={}
        for task_id , data in task_groups.items():
            scores=data["scores"]
            if not scores:
                continue
            if all(s<threshold for s in scores):
                cat = data["category"]
                if cat not in failed_by_category:
                    failed_by_category[cat]=[]
                failed_by_category[cat].append({"id":task_id,"question":data["question"]})

    return failed_by_category

async def run_evolution()->dict:
    failed_categories=get_failed_categories(threshold=5.0)
    if not failed_categories:
        return {"message" : "No failed catgories found. All models performing well."}
    with open ("task/task_libarary.json","r") as f:
        existing_tasks=json.load(f)
    existing_ids={t["id"] for t in existing_tasks}
    total_added = 0
    summary={}

    for category, failed_tasks in failed_categories.items():
        print(f"Evolving Category : {category} ({len(failed_tasks)} failed tasks)")
        new_questions=await generate_harder_questions(category,failed_tasks)
        added =0
        for q in new_questions:
            if q["id"] not in existing_ids:
                existing_tasks.append(q)
                existing_ids.add(q["id"])
                added+=1

        total_added += added
        summary[category]={"failed_tasks":len(failed_tasks),"new_questions_added":added}

    with open("tasks/task_library.json","w") as f:
            json.dump(existing_tasks,f,indent =2 )
    return {"total_new_questions":total_added,"categories_evolved":summary}

