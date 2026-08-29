import os
import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
from dotenv import load_dotenv

load_dotenv()

from app.tools import search_kb


def load_eval_set(path="data/eval_set.json"):
  with open(path, "r", encoding="utf-8") as f:
      return json.load(f)


def run_eval(eval_set):
  hit = 0
  total = len(eval_set)
  for item in eval_set:
      q, expect = item["query"], item["expect"]
      result = search_kb.func(q)          # .func 拿原始函数直接调
      if expect in result:
          hit += 1
          print(f"✅ {q}")
      else:
          print(f"❌ {q}  → 期望含「{expect}」，实际：{result[:50]}")
  rate = hit / total
  print(f"\n命中率 = {hit}/{total} = {rate:.1%}")
  return rate


if __name__ == "__main__":
  eval_set = load_eval_set()
  for th in ["0.9", "0.7", "0.5", "1.0"]:
      os.environ["SEARCH_KB_THRESHOLD"] = th
      print(f"\n===== 阈值 {th} =====")
      run_eval(eval_set)