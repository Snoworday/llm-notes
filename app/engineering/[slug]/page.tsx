import { getAllPosts, getPostBySlug } from "@/lib/posts";
import { notFound } from "next/navigation";
import Link from "next/link";

export async function generateStaticParams() {
  return getAllPosts("engineering").map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const post = await getPostBySlug("engineering", params.slug);
  if (!post) return {};
  return { title: `${post.meta.title} · LLM Notes` };
}

export default async function EngineeringDetail({
  params,
}: {
  params: { slug: string };
}) {
  const post = await getPostBySlug("engineering", params.slug);
  if (!post) notFound();

  return (
    <article className="max-w-3xl mx-auto px-6 py-16">
      <Link
        href="/engineering"
        className="text-sm text-ink-500 hover:text-ink-900 transition"
      >
        ← 返回工程实践
      </Link>

      <header className="mt-8 pb-8 border-b border-[#ececec]">
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight leading-tight">
          {post.meta.title}
        </h1>
        <div className="mt-4 flex items-center gap-3 text-sm text-ink-500">
          <span className="tabular-nums">{post.meta.date}</span>
          {post.meta.tags?.map((t) => (
            <span key={t} className="px-1.5 py-0.5 bg-ink-100 rounded text-xs">
              {t}
            </span>
          ))}
        </div>
        {post.meta.link && (
          <a
            href={post.meta.link}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-sm text-accent hover:underline"
          >
            参考链接 ↗
          </a>
        )}
      </header>

      <div
        className="prose-custom mt-10"
        dangerouslySetInnerHTML={{ __html: post.html }}
      />
    </article>
  );
}
