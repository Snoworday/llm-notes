export const metadata = { title: "关于 · LLM Notes" };

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-20">
      <h1 className="text-3xl font-semibold tracking-tight">关于</h1>
      <div className="mt-8 space-y-5 text-ink-700 leading-relaxed">
        <p>
          这是一个用来收集、记录、分享 LLM 方向最新前沿论文与工程实践的小站。
        </p>
        <p>
          内容方向涵盖:
        </p>
        <ul className="list-disc pl-6 space-y-1 text-ink-700">
          <li>大语言模型预训练 / 后训练 (SFT, RLHF, DPO, GRPO ...)</li>
          <li>推理能力 (CoT, ToT, Reasoning Models)</li>
          <li>Agent 框架与工具使用</li>
          <li>推理加速、显存优化、模型压缩</li>
          <li>评测、对齐、安全</li>
        </ul>
        <p className="text-ink-500 text-sm pt-4 border-t border-[#ececec] mt-8">
          联系: 待补充
        </p>
      </div>
    </div>
  );
}
