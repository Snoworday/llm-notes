import Link from "next/link";
import { getAllPosts } from "@/lib/posts";

export const metadata = { title: "论文 · LLM Notes" };

export default function PapersPage() {
  const posts = getAllPosts("papers");

  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold tracking-tight">论文笔记</h1>
        <p className="text-ink-500 mt-3 text-sm">
          LLM 方向的论文阅读笔记,持续更新。
        </p>
      </div>

      {posts.length === 0 ? (
        <p className="text-ink-500 text-sm">暂无内容</p>
      ) : (
        <ul className="space-y-7 border-t border-[#ececec] pt-8">
          {posts.map((p) => (
            <li key={p.slug}>
              <Link href={`/papers/${p.slug}`} className="block group">
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
                    {p.tags && p.tags.length > 0 && (
                      <div className="flex gap-2 mt-2">
                        {p.tags.map((t) => (
                          <span
                            key={t}
                            className="text-xs text-ink-500 px-1.5 py-0.5 bg-ink-100 rounded"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
