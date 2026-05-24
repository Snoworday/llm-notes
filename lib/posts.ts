import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";

const contentRoot = path.join(process.cwd(), "content");

export type PostMeta = {
  slug: string;
  title: string;
  date: string;
  summary?: string;
  tags?: string[];
  category: "papers" | "engineering";
  link?: string;
};

export function getAllPosts(category?: "papers" | "engineering"): PostMeta[] {
  const categories: ("papers" | "engineering")[] = category
    ? [category]
    : ["papers", "engineering"];

  const all: PostMeta[] = [];
  for (const cat of categories) {
    const dir = path.join(contentRoot, cat);
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md"));
    for (const file of files) {
      const slug = file.replace(/\.md$/, "");
      const raw = fs.readFileSync(path.join(dir, file), "utf-8");
      const { data } = matter(raw);
      all.push({
        slug,
        title: data.title || slug,
        date: data.date || "",
        summary: data.summary || "",
        tags: data.tags || [],
        category: cat,
        link: data.link || "",
      });
    }
  }
  return all.sort((a, b) => (a.date < b.date ? 1 : -1));
}

export async function getPostBySlug(
  category: "papers" | "engineering",
  slug: string
) {
  const file = path.join(contentRoot, category, `${slug}.md`);
  if (!fs.existsSync(file)) return null;
  const raw = fs.readFileSync(file, "utf-8");
  const { data, content } = matter(raw);
  const processed = await remark().use(remarkGfm).use(remarkHtml).process(content);
  return {
    meta: {
      slug,
      title: data.title || slug,
      date: data.date || "",
      summary: data.summary || "",
      tags: data.tags || [],
      category,
      link: data.link || "",
    } as PostMeta,
    html: processed.toString(),
  };
}
