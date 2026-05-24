---
title: "vLLM PagedAttention 工程实践笔记"
date: "2025-03-10"
summary: "vLLM 通过 PagedAttention 大幅提升推理吞吐,实际部署中的几个关键参数与坑。"
tags: ["Inference", "vLLM", "Serving"]
link: "https://github.com/vllm-project/vllm"
---

## 为什么需要 PagedAttention

传统 KV Cache 按最大序列长度连续分配,导致:

- **内部碎片**: 实际序列短,但预留空间大
- **外部碎片**: 不同 batch 之间难以共享
- 显存利用率往往 < 40%

PagedAttention 借鉴操作系统虚拟内存的思路,把 KV Cache 切成固定大小的 block,按需分配。

## 关键启动参数

```bash
vllm serve <model> \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 32768 \
  --enable-prefix-caching \
  --max-num-seqs 256
```

## 几个常见的坑

### 1. gpu-memory-utilization 不是越高越好

设到 0.95+ 容易 OOM,因为还要给临时激活、CUDA Graph 留空间。推荐 0.85 ~ 0.92。

### 2. enable-prefix-caching 在共享 system prompt 场景收益巨大

agent / RAG 场景能直接降 30-50% 的 TTFT。

### 3. Chunked Prefill

长 prompt 场景务必开启 `--enable-chunked-prefill`,否则会阻塞 decoding,导致 ITL 抖动。

## 性能调优顺序

1. 先确认是 compute-bound 还是 memory-bound
2. 调 `max-num-batched-tokens` 找拐点
3. 开 prefix caching + chunked prefill
4. 考虑量化 (AWQ / FP8)
5. 最后再考虑 speculative decoding
