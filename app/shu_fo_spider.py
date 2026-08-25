import requests
import time
import json
import csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://shu.fo/"
}

BASE_URL = "https://shu.fo/api/v1/document/list"


def fetch_documents(target_count=100, page_size=20):
    """分页抓取文档列表，直到凑够 target_count 条"""
    result = []
    page = 1

    while len(result) < target_count:
        params = {"page": page, "size": page_size}
        try:
            resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            docs = data.get("document", [])
            if not docs:
                print(f"第 {page} 页无数据，停止抓取")
                break

            for doc in docs:
                if len(result) >= target_count:
                    break
                result.append(clean_document(doc))

            total = data.get("total", 0)
            print(f"已抓取第 {page} 页，累计 {len(result)}/{target_count} 条（全站共 {total} 条）")
            page += 1
            time.sleep(0.8)  # 限速，防止被封IP

        except requests.exceptions.RequestException as e:
            print(f"第 {page} 页请求失败: {e}，2秒后重试...")
            time.sleep(2)
            continue
        except (KeyError, ValueError) as e:
            print(f"第 {page} 页数据解析异常: {e}")
            break

    return result[:target_count]


def clean_document(doc):
    """清洗单条文档数据，提取结构化字段"""
    # 分类名称拼接
    categories = doc.get("category", [])
    category_names = " > ".join([c.get("title", "") for c in categories]) if categories else ""

    # 文件大小转 MB
    size_bytes = doc.get("size", 0)
    size_mb = round(size_bytes / 1024 / 1024, 2) if size_bytes else 0

    # 描述截断（避免过长），去除多余空白
    description = doc.get("description", "") or ""
    description = " ".join(description.split())[:200]

    return {
        "id": doc.get("id"),
        "title": doc.get("title", "").strip(),
        "keywords": doc.get("keywords", ""),
        "category": category_names,
        "language": doc.get("language", ""),
        "pages": doc.get("pages", 0),
        "file_ext": doc.get("ext", ""),
        "file_size_mb": size_mb,
        "download_count": doc.get("download_count", 0),
        "view_count": doc.get("view_count", 0),
        "score": doc.get("score", 0),
        "price": doc.get("price", 0),
        "uploader": doc.get("username", ""),
        "created_at": doc.get("created_at", ""),
        "uuid": doc.get("uuid", ""),
        "detail_url": f"https://shu.fo/document/{doc.get('uuid', '')}",
        "description": description
    }


def save_to_json(data, filename="shu_fo_100.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存 JSON: {filename}（共 {len(data)} 条）")


def save_to_csv(data, filename="shu_fo_100.csv"):
    if not data:
        return
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"已保存 CSV: {filename}（共 {len(data)} 条）")


if __name__ == "__main__":
    print("开始抓取 shu.fo 文档列表...")
    documents = fetch_documents(target_count=100, page_size=20)

    save_to_json(documents, "../data/shu_fo_100.json")
    save_to_csv(documents, "../data/shu_fo_100.csv")

    # 打印前3条预览
    print("\n=== 数据预览（前3条）===")
    for i, doc in enumerate(documents[:3], 1):
        print(f"\n[{i}] {doc['title'][:60]}")
        print(f"    分类: {doc['category']} | 页数: {doc['pages']} | 大小: {doc['file_size_mb']}MB")
        print(f"    上传者: {doc['uploader']} | 浏览: {doc['view_count']} | 下载: {doc['download_count']}")
