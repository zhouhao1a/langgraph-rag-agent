import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"   # 必须在 import tools 之前

from tools import get_weather, scrape_web

print("=== get_weather ===")
print(get_weather.invoke({"city": "深圳"}))

print("\n=== scrape_web ===")
text = scrape_web.invoke({ "url": "https://example.com/no_such_pag"})
print(text[:200])
