import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "LLM Notes — 前沿论文与工程实践",
  description: "记录与分享大语言模型方向的最新论文、工程实践与思考。",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-[#ececec]">
          <nav className="max-w-3xl mx-auto px-6 py-6 flex items-center justify-between">
            <Link href="/" className="text-base font-semibold tracking-tight">
              LLM Notes
            </Link>
            <div className="flex items-center gap-7 text-sm text-ink-500">
              <Link href="/papers" className="hover:text-ink-900 transition">论文</Link>
              <Link href="/engineering" className="hover:text-ink-900 transition">工程</Link>
              <Link href="/about" className="hover:text-ink-900 transition">关于</Link>
            </div>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-[#ececec] mt-20">
          <div className="max-w-3xl mx-auto px-6 py-8 text-xs text-ink-500 flex items-center justify-between">
            <span>© {new Date().getFullYear()} LLM Notes</span>
            <span>Built with Next.js · Deployed on Vercel</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
