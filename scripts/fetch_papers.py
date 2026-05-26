"""
每日自动抓取 arXiv 上 LLM 方向的最新论文,用 LLM 生成中文摘要,
保存为 Markdown 文件到 content/papers/ 目录。
"""

import os
import re
import time
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# ============ 配置 ============

# arXiv 分类 + 关键词,只抓 LLM 相关
ARXIV_CATEGORIES = ["cs.CL", "cs.AI", "cs.LG"]
KEYWORDS = [
    "large language model", "LLM", "transformer", "reasoning",
    "agent", "RLHF", "DPO", "GRPO", "fine-tuning", "instruction tuning",
    "in-context learning", "chain of thought", "mixture of experts",
    "retrieval augmented", "RAG", "long context", "inference",
]

# 每天最多处理几篇(防止 API 配额爆掉)
MAX_PAPERS_PER_RUN = 5

# 输出目录
OUTPUT_DIR = Path("content/papers")
HISTORY_FILE = Path("scripts/.processed.json")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
# LLM API 配置 (DeepSeek)
# LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
# LLM_MODEL = "deepseek-chat"

LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_MODEL = "gpt-4o-mini"   # 或者 gpt-4o / gpt-4.1-mini


# ============ arXiv 抓取 ============

def fetch_arxiv_papers(max_retries=5):
    """抓取最新的 arXiv 论文。带礼貌的 User-Agent 和指数退避重试。"""
    cat_query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query={cat_query}"
        "&sortBy=submittedDate&sortOrder=descending"
        "&max_results=100"
    )
    headers = {
        # arXiv 要求 UA 里带项目名 / 联系方式
        "User-Agent": "llm-notes-bot/1.0 (https://github.com/Snoworday/llm-notes)",
        "Accept": "application/atom+xml",
    }
    print(f"[arxiv] fetching: {url}")

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 503):
                wait = min(60, 5 * (2 ** (attempt - 1)))  # 5,10,20,40,60
                print(f"[arxiv] HTTP {e.code}, retry {attempt}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            wait = 5 * attempt
            print(f"[arxiv] error {e!r}, retry {attempt}/{max_retries} after {wait}s")
            time.sleep(wait)
    else:
        raise RuntimeError(f"arxiv fetch failed after {max_retries} retries: {last_err}")

    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    papers = []
    for entry in root.findall("a:entry", ns):
        title = entry.find("a:title", ns).text.strip().replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        summary = entry.find("a:summary", ns).text.strip().replace("\n", " ")
        summary = re.sub(r"\s+", " ", summary)
        link = entry.find("a:id", ns).text.strip()
        pub = entry.find("a:published", ns).text.strip()
        authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
        papers.append({
            "title": title,
            "abstract": summary,
            "link": link,
            "published": pub,
            "authors": authors[:5],
        })
    print(f"[arxiv] got {len(papers)} entries")
    return papers

def filter_papers(papers, processed_ids):
    """关键词过滤 + 去重"""
    filtered = []
    for p in papers:
        text = (p["title"] + " " + p["abstract"]).lower()
        if not any(k.lower() in text for k in KEYWORDS):
            continue
        pid = p["link"].split("/")[-1]
        if pid in processed_ids:
            continue
        p["id"] = pid
        filtered.append(p)
    print(f"[filter] {len(filtered)} new papers after filtering")
    return filtered[:MAX_PAPERS_PER_RUN]


# ============ LLM 摘要 ============

def llm_summarize(paper):
    """用 LLM 生成中文摘要"""
    prompt = f"""你是一位 LLM 方向的资深研究员。请用中文为以下论文生成一份精炼笔记。

论文标题: {paper['title']}
论文摘要: {paper['abstract']}

请按下面的格式输出 Markdown,不要有任何额外的解释:

## 一句话总结
(用一句话讲清楚这篇论文做了什么)

## 核心问题
(论文要解决什么问题,为什么这个问题重要)

## 关键方法
(用 2-4 个要点说明方法的核心创新)

## 主要结果
(主要实验结论,只列最关键的)

## 个人看法
(这篇论文的意义、可能的应用场景、潜在局限)
"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是 LLM 方向的资深研究员,擅长用精炼的中文表达技术细节。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        LLM_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()


# ============ Markdown 生成 ============

def slugify(title):
    s = re.sub(r"[^\w\s-]", "", title.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:60]


def extract_tags(paper):
    text = (paper["title"] + " " + paper["abstract"]).lower()
    tag_map = {
        "Reasoning": ["reasoning", "chain of thought", "cot"],
        "RL": ["rlhf", "dpo", "grppo", "reinforcement"],
        "Agent": ["agent", "tool use"],
        "RAG": ["retrieval", "rag"],
        "Inference": ["inference", "serving", "vllm"],
        "MoE": ["mixture of experts", "moe"],
        "Fine-tuning": ["fine-tuning", "sft", "instruction tuning"],
        "Long Context": ["long context", "long-context"],
    }
    tags = []
    for tag, kws in tag_map.items():
        if any(k in text for k in kws):
            tags.append(tag)
    return tags or ["LLM"]


def save_paper(paper, summary):
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    slug = f"{paper['id']}-{slugify(paper['title'])}"
    tags = extract_tags(paper)
    safe_title = paper["title"].replace('"', "'")
    safe_abs = paper["abstract"][:200].replace('"', "'").replace("\n", " ")

    fm = (
        "---\n"
        f'title: "{safe_title}"\n'
        f'date: "{today}"\n'
        f'summary: "{safe_abs}..."\n'
        f"tags: {json.dumps(tags)}\n"
        f'link: "{paper["link"]}"\n'
        "---\n\n"
    )
    body = (
        f"> **作者**: {', '.join(paper['authors'])}\n"
        f"> **发布**: {paper['published'][:10]}\n"
        f"> **arXiv**: [{paper['id']}]({paper['link']})\n\n"
        f"{summary}\n"
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{slug}.md"
    out.write_text(fm + body, encoding="utf-8")
    print(f"[save] {out}")
    return slug


# ============ 历史去重 ============

def load_history():
    if HISTORY_FILE.exists():
        return set(json.loads(HISTORY_FILE.read_text()))
    return set()


def save_history(ids):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(sorted(ids), indent=2))


# ============ 主流程 ============

def main():
    if not LLM_API_KEY:
        raise SystemExit("LLM_API_KEY not set")

    processed = load_history()
    papers = fetch_arxiv_papers()
    selected = filter_papers(papers, processed)

    if not selected:
        print("nothing new to process today")
        return

    for p in selected:
        try:
            print(f"[summarize] {p['title'][:80]}")
            summary = llm_summarize(p)
            save_paper(p, summary)
            processed.add(p["id"])
            time.sleep(2)
        except Exception as e:
            print(f"[error] {p['id']}: {e}")

    save_history(processed)
    print("done")


if __name__ == "__main__":
    main()
