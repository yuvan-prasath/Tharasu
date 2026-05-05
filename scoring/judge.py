import json
import re
from litellm import acompletion
from config import JUDGE_MODEL

JUDGE_PROMPT = """You are an expert evaluator assessing AI model responses.

Question: {question}

Answer to evaluate: {answer}

Rate this answer strictly from 1 to 10 based on correctness, clarity, and completeness.
Return ONLY a valid JSON object with no extra text, no markdown, no explanation outside the JSON.
Format: {{"score": <integer 1-10>, "reason": "<one sentence>"}}"""

async def judge_answer(question:str,answer:str)->dict:

    if not answer:
        return {"Score" : 1.0, "reason":"No answer provided"}
    prompt = JUDGE_PROMPT.format(question=question,answer=answer[:1500])
    try:
        response = await acompletion(model=JUDGE_MODEL,messages=[{"role":"user","content":prompt}],max_tokens=150,temperature=0.1)
        raw=response.choices[0].message.content.strip()
        raw=re.sub(r"```json|```","",raw).strip()
        parsed=json.loads(raw)
        score=float(parsed.get("score",5))
        score=max(1.0,min(10.0,score))
        reason=parsed.get("reason","No reason provided")
        return {"score":score,"reason":reason}
    except json.JSONDecodeError:
        nums=re.findall(r"\b([1-9]|10)\b",raw)
        score=float(nums[0])
        return {"score":score,"reason":"Parsed from raw output"}

    except Exception as e:
        return {"score":5.0,"reason":f"Judge error:{str(e)[:80]}"}


