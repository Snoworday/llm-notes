import Link from "next/link";
import { getAllPosts } from "@/lib/posts";

export default function Home() {
  const posts = getAllPosts().slice(0, 8);

  return (
    <div className="max-w-3xl mx-auto px-6">
      {/* Hero */}
      <section className="pt-24 pb-20 border-b border-[#ececec]">
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight leading-tight">
          记录 LLM 的<br />前沿与实践
        </h1>
        <p className="mt-6 text-ink-500 text-base leading-relaxed max-w-xl">
          这里是我整理的大语言模型方向的论文笔记、工程实践与思考。
          关注 Reasoning、Agent、Post-training、Inference 等方向。
        </p>
        <div className="mt-8 flex gap-5 text-sm">
          <Link
            href="/papers"
            className="inline-flex items-center px-4 py-2 border border-ink-900 text-ink-900 hover:bg-ink-900 hover:text-white transition"
          >
            浏览论文
          </Link>
          <Link
            href="/engineering"
            className="inline-flex items-center px-4 py-2 text-ink-700 hover:text-ink-900 transition"
          >
            工程实践 →
          </Link>
        </div>
      </section>

      {/* Latest */}
      <section className="py-16">
        <div className="flex items-baseline justify-between mb-8">
          <h2 className="text-xl font-semibold tracking-tight">最近更新</h2>
          <Link href="/papers" className="text-sm text-ink-500 hover:text-ink-900">
            查看全部 →
          </Link>
        </div>

        {posts.length === 0 ? (
          <p className="text-ink-500 text-sm">
            还没有内容,在{" "}
            <code className="bg-ink-100 px-1.5 py-0.5 rounded text-xs">
              content/papers
            </code>{" "}
            或{" "}
            <code className="bg-ink-100 px-1.5 py-0.5 rounded text-xs">
              content/engineering
            </code>{" "}
            目录中添加 Markdown 文件即可。
          </p>
        ) : (
          <ul className="space-y-7">
            {posts.map((p) => (
              <li key={`${p.category}-${p.slug}`} className="group">
                <Link href={`/${p.category}/${p.slug}`} className="block">
                  <div className="flex items-baseline gap-4">
                    <span className="text-xs text-ink-500 tabular-nums shrink-0 w-24">
                      {p.date}
                    </span>
                    <div className="flex-1">
                      <h3 className="text-base font-medium group-hover:underline underline-offset-4">
                        {p.title}
                      </h3>
                      {p.summary && (
                        <p className="text-sm text-ink-500 mt-1 leading-relaxed">
                          {p.summary}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-ink-500 uppercase tracking-wider">
                          {p.category === "papers" ? "Paper" : "Engineering"}
                        </span>
                        {p.tags?.slice(0, 3).map((t) => (
                          <span
                            key={t}
                            className="text-xs text-ink-500 px-1.5 py-0.5 bg-ink-100 rounded"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
