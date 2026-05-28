"""
每日自动抓取 LLM 方向的最新论文,用 LLM 生成中文摘要,
保存为 Markdown 文件到 content/papers/ 目录。

数据源(按优先级):
  1. Hugging Face Daily Papers - 社区精选,质量高,无频控
  2. arXiv RSS - 备用源,无频控

LLM 后端: OpenAI-compatible Chat Completions API
"""

import os
import re
import time
import json
import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# ============ 配置 ============

# 每天最多处理几篇(防止 API 配额爆掉)
MAX_PAPERS_PER_RUN = 5

# 输出目录
OUTPUT_DIR = Path("content/papers")
HISTORY_FILE = Path("scripts/.processed.json")

# arXiv RSS 备用源(分类)
ARXIV_RSS_CATEGORIES = ["cs.CL", "cs.AI", "cs.LG"]

# 关键词过滤(用于 arXiv RSS 备用源)
KEYWORDS = [
    "large language model", "llm", "transformer", "reasoning",
    "agent", "rlhf", "dpo", "grpo", "fine-tuning", "instruction tuning",
    "in-context learning", "chain of thought", "mixture of experts",
    "retrieval augmented", "rag", "long context", "inference",
    "diffusion language", "alignment", "post-training",
]

# LLM API 配置 (OpenAI 兼容)
LLM_API_URL = os.environ.get(
    "LLM_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions"
)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4.5-flash")


# ============ 通用 HTTP ============

def http_get(url, headers=None, timeout=60, max_retries=3):
    """带重试的 GET"""
    headers = headers or {}
    headers.setdefault(
        "User-Agent",
        "llm-notes-bot/1.0 (https://github.com/Snoworday/llm-notes)",
    )
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 503):
                wait = 5 * (2 ** (attempt - 1))
                print(f"[http] {url} -> HTTP {e.code}, retry {attempt}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            wait = 5 * attempt
            print(f"[http] {url} -> {e!r}, retry {attempt}/{max_retries} after {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"failed after {max_retries} retries: {last_err}")


# ============ 数据源 1: Hugging Face Daily Papers ============

def fetch_hf_daily_papers():
    """抓 Hugging Face Daily Papers, 抓最近 3 天 (有的天数没榜单)"""
    all_papers = []
    today = datetime.now(timezone(timedelta(hours=8)))
    for day_offset in range(0, 4):
        d = today - timedelta(days=day_offset)
        date_str = d.strftime("%Y-%m-%d")
        url = f"https://huggingface.co/api/daily_papers?date={date_str}"
        try:
            print(f"[hf] fetching {date_str}")
            data = http_get(url)
            items = json.loads(data)
        except Exception as e:
            print(f"[hf] {date_str} failed: {e}")
            continue
        if not isinstance(items, list):
            continue
        for it in items:
            p = it.get("paper") or {}
            arxiv_id = p.get("id") or it.get("arxivId")
            if not arxiv_id:
                continue
            authors = []
            for a in p.get("authors", [])[:5]:
                if isinstance(a, dict):
                    authors.append(a.get("name", ""))
                else:
                    authors.append(str(a))
            all_papers.append({
                "id": arxiv_id,
                "title": (p.get("title") or it.get("title") or "").strip(),
                "abstract": (p.get("summary") or p.get("abstract") or "").strip(),
                "link": f"https://arxiv.org/abs/{arxiv_id}",
                "published": p.get("publishedAt") or it.get("publishedAt") or date_str,
                "authors": authors,
                "_source": "hf-daily",
                "_hf_upvotes": p.get("upvotes", 0) or it.get("upvotes", 0),
            })
    # 去重 + 按 HF 热度排
    seen = set()
    uniq = []
    for p in sorted(all_papers, key=lambda x: x.get("_hf_upvotes", 0), reverse=True):
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
    print(f"[hf] got {len(uniq)} unique papers")
    return uniq


# ============ 数据源 2: arXiv RSS (备用) ============

def fetch_arxiv_rss():
    """从 arXiv RSS 拉取最新论文 (备用)"""
    all_papers = []
    for cat in ARXIV_RSS_CATEGORIES:
        url = f"https://rss.arxiv.org/rss/{cat}"
        try:
            print(f"[arxiv-rss] fetching {cat}")
            xml_data = http_get(url)
        except Exception as e:
            print(f"[arxiv-rss] {cat} failed: {e}")
            continue
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            print(f"[arxiv-rss] parse {cat} failed: {e}")
            continue
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip().replace("\n", " ")
            title = re.sub(r"\s+", " ", title)
            desc = (item.findtext("description") or "").strip().replace("\n", " ")
            desc = re.sub(r"\s+", " ", desc)
            link = (item.findtext("link") or "").strip()
            m = re.search(r"abs/(\d{4}\.\d{4,5})", link)
            if not m:
                continue
            arxiv_id = m.group(1)
            all_papers.append({
                "id": arxiv_id,
                "title": title,
                "abstract": desc,
                "link": link,
                "published": item.findtext("pubDate") or "",
                "authors": [],
                "_source": "arxiv-rss",
            })
    # 去重 + 关键词过滤
    seen = set()
    uniq = []
    for p in all_papers:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        text = (p["title"] + " " + p["abstract"]).lower()
        if not any(k in text for k in KEYWORDS):
            continue
        uniq.append(p)
    print(f"[arxiv-rss] {len(uniq)} unique LLM papers after filtering")
    return uniq


# ============ LLM 摘要 ============

def llm_summarize(paper):
    """用 LLM 生成中文摘要"""
    prompt = f"""你是一位 LLM 方向的资深研究员。请用中文为以下论文生成一份精炼笔记。

论文标题: {paper['title']}
论文摘要: {paper['abstract']}

请按下面的格式输出 Markdown,不要有任何额外的解释或代码块包裹:

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
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()


# ============ Markdown 生成 ============

def slugify(title):
    s = re.sub(r"[^\w\s-]", "", title.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:50]


def extract_tags(paper):
    text = (paper["title"] + " " + paper["abstract"]).lower()
    tag_map = {
        "Reasoning": ["reasoning", "chain of thought", "cot ", "cot,", "thinking"],
        "RL": ["rlhf", "dpo", "grpo", "reinforcement"],
        "Agent": ["agent", "tool use", "tool-use"],
        "RAG": ["retrieval", "rag "],
        "Inference": ["inference", "serving", "vllm", "kv cache"],
        "MoE": ["mixture of experts", "moe "],
        "Fine-tuning": ["fine-tuning", "instruction tuning", " sft "],
        "Long Context": ["long context", "long-context"],
        "Alignment": ["alignment", "preference"],
        "Multimodal": ["multimodal", "vision-language", "vlm"],
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
    safe_title = paper["title"].replace('"', "'").replace("\\", " ")
    abs_text = paper["abstract"][:180].replace('"', "'").replace("\n", " ")

    fm = (
        "---\n"
        f'title: "{safe_title}"\n'
        f'date: "{today}"\n'
        f'summary: "{abs_text}..."\n'
        f"tags: {json.dumps(tags)}\n"
        f'link: "{paper["link"]}"\n'
        "---\n\n"
    )
    authors = ", ".join(paper["authors"]) if paper["authors"] else "(see arXiv)"
    pub = (paper.get("published") or "")[:10]
    body = (
        f"> **作者**: {authors}\n"
        f"> **发布**: {pub}\n"
        f"> **arXiv**: [{paper['id']}]({paper['link']})\n"
        f"> **来源**: {paper.get('_source', 'unknown')}\n\n"
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
    # 优先 HF Daily Papers
    papers = []
    try:
        papers = fetch_hf_daily_papers()
    except Exception as e:
        print(f"[hf] failed entirely: {e}")
    # 不足时用 arXiv RSS 补
    if len(papers) < MAX_PAPERS_PER_RUN:
        try:
            papers += fetch_arxiv_rss()
        except Exception as e:
            print(f"[arxiv-rss] failed: {e}")

    # 去重 + 去已处理
    seen = set()
    fresh = []
    for p in papers:
        if p["id"] in seen or p["id"] in processed:
            continue
        seen.add(p["id"])
        fresh.append(p)
    selected = fresh[:MAX_PAPERS_PER_RUN]
    print(f"[main] {len(selected)} papers to process")

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
            print(f"[error] {p['id']}: {e!r}")

    save_history(processed)
    print("done")


if __name__ == "__main__":
    main()