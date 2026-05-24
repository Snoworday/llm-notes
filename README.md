# LLM Notes

极简风格的个人网站,用于收集、记录、分享 LLM 方向的最新论文与工程实践。

技术栈:Next.js 14 (App Router) + TailwindCSS + Markdown。

---

## 目录结构

```
llm-notes/
├── app/                    # Next.js 路由
│   ├── page.tsx            # 首页
│   ├── papers/             # 论文列表 + 详情
│   ├── engineering/        # 工程实践列表 + 详情
│   └── about/              # 关于
├── content/                # 写作内容
│   ├── papers/             # 论文笔记 (.md)
│   └── engineering/        # 工程笔记 (.md)
├── lib/posts.ts            # Markdown 解析
└── ...
```

---

## 本地运行

```bash
npm install
npm run dev
# 访问 http://localhost:3000
```

---

## 写一篇新笔记

在 `content/papers/` 或 `content/engineering/` 下新建 `.md` 文件:

```markdown
---
title: "论文/文章标题"
date: "2025-05-23"
summary: "一句话摘要"
tags: ["Reasoning", "RL"]
link: "https://arxiv.org/abs/xxxx"
---

## 章节标题

正文内容,支持完整 Markdown 语法。
```

保存后,首页和列表页会自动展示,无需重启。

---

## 部署到 Vercel(完全免费)

### 步骤 1: 推送到 GitHub

```bash
cd llm-notes
git init
git add .
git commit -m "init"
# 在 GitHub 上创建仓库 llm-notes,然后:
git remote add origin git@github.com:<your-username>/llm-notes.git
git push -u origin main
```

### 步骤 2: 部署到 Vercel

1. 访问 [vercel.com](https://vercel.com),用 GitHub 登录
2. 点击 **Add New → Project**
3. 选择刚才创建的 `llm-notes` 仓库
4. 全部用默认配置,点 **Deploy**
5. 大约 1-2 分钟,网站就上线了,Vercel 会给你一个 `xxx.vercel.app` 的域名

之后每次 `git push`,Vercel 都会自动重新构建部署。

### 步骤 3(可选): 绑定自定义域名

在 Vercel 项目 → Settings → Domains 添加你自己的域名,按提示改 DNS 即可。
