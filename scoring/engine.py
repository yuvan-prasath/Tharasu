from nltk.translate.bleu_score import sentence_bleu,SmoothingFunction
import re
import nltk
nltk.download('punkt')

def calculate_accuracy(answer:str,expected:str)->float:
    if not answer or not expected:
        return None
    answer_clean=answer.strip().lower()
    expected_clean=expected.strip().lower()
    if expected_clean in answer_clean:
        return 100.0
    answer_nums=re.findall(r"-?\d+\.?\d*",answer_clean)
    expected_nums=re.findall(r"-?\d+\.?\d*",expected_clean)
    if expected_nums and answer_nums:
        if expected_nums[0] in answer_nums:
            return 100.0
    return 0.

def calculate_bleu(answer:str,reference:str)->float:
    if not answer or not reference:
        return None
    smoothie=SmoothingFunction().method1
    score=sentence_bleu([reference.split()],answer.split(),smoothing_function=smoothie)
    return round(score,4)

def calculate_tharasu_score(accuracy:float,judge_score:float,latency_ms:float,tokens_used:float,bleu_score:float,all_latencies:list,all_tokens:list)->float:
    acc=accuracy if accuracy is not None else 50.0
    judge=((judge_score-1)/9)*100 if judge_score is not None else 50.0
    if all_latencies and latency_ms is not None:
        min_lat=min(all_latencies)
        max_lat=max(all_latencies)
        if max_lat==min_lat:
            speed=100.0
        else:
            speed=((max_lat-min_lat)/(max_lat-min_lat))*100
    else:
        speed=50
    if all_tokens and tokens_used is not None:
        min_tok = min(all_tokens)
        max_tok = max(all_tokens)
        if max_tok==min_tok:
            token_eff =100.0
        else:
            token_eff = ((max_tok-tokens_used)/(max_tok-min_tok))*100
    else:
        token_eff = 50.0
    bleu=(bleu_score*100) if bleu_score is not None else 50.0
    score=(acc*0.35+judge*0.30+speed*0.15+token_eff*0.10+bleu*0.10)
    return round(score,2)
