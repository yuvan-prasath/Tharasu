from dotenv import load_dotenv
load_dotenv()

import asyncio
import time
import json
import os
from litellm import acompletion
from config import MODELS

async def ask_model(model_name: str, model_id: str, question: str):
    start = time.time()
    try:
        response = await acompletion(
            model=model_id,
            messages=[{"role": "user", "content": question}],
            max_tokens=500
        )
        latency = round((time.time() - start) * 1000, 2)
        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens

        return {
            "model": model_name,
            "answer": answer,
            "latency": latency,
            "tokens": tokens,
            "status": "success"
        }

    except Exception as e:
        return {
            "model": model_name,
            "answer": None,
            "latency": None,
            "tokens": None,
            "status": f"error: {str(e)[:80]}"
        }

async def run_benchmark(question: str):
    print(f"\n{'='*60}")
    print(f"QUESTION: {question}")
    print(f"{'='*60}")

    tasks = [
        ask_model(name, model_id, question)
        for name, model_id in MODELS.items()
    ]

    results = await asyncio.gather(*tasks)

    for r in results:
        status = "✓" if r["status"] == "success" else "✗"
        print(f"\n{status} MODEL   : {r['model']}")
        print(f"  LATENCY : {r['latency']}ms")
        print(f"  TOKENS  : {r['tokens']}")
        print(f"  ANSWER  : {r['answer'][:200] if r['answer'] else r['status']}")

    return results

async def main():
    with open("tasks/task_library.json") as f:
        tasks = json.load(f)

    for task in tasks[:2]:
        await run_benchmark(task["question"])
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())