import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY or ""

MODELS = {
    "llama3_70b":  "groq/llama-3.3-70b-versatile",
    "llama3_8b":   "groq/llama-3.1-8b-instant",
    "llama4_scout": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen3":       "groq/qwen/qwen3-32b",
}

JUDGE_MODEL="groq/llama-3.3-70b-versatile"
SCORE_WEIGHTS = {"accuracy":0.35,"judge":0.30,"speed":0.15,"tokens":0.10,"bleu":0.10,}

BENCHMARK_CATEGORIES = ["math", "coding", "reasoning"]