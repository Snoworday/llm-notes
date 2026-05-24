---
title: "DeepSeek-R1: 通过强化学习激发推理能力"
date: "2025-01-22"
summary: "DeepSeek-R1 通过纯强化学习 (GRPO) 训练激发模型的长链推理能力,无需大规模 SFT 数据冷启动。"
tags: ["Reasoning", "RL", "GRPO"]
link: "https://arxiv.org/abs/2501.12948"
---

## 核心观点

DeepSeek-R1 提出了一种**无需 SFT 冷启动**的纯强化学习训练方式 (R1-Zero),证明了仅通过 RL 也能让基础模型自发涌现出长链推理 (Long CoT) 与反思 (Reflection) 能力。

## 方法

### R1-Zero

- 基础模型: DeepSeek-V3-Base
- RL 算法: **GRPO** (Group Relative Policy Optimization)
- 奖励信号: 规则奖励 (准确性 + 格式)
- 关键发现: 模型在训练过程中自发出现 "aha moment",即开始反思自己的推理过程

### R1

为了缓解 R1-Zero 的可读性问题,引入了多阶段训练:

1. 用少量长 CoT 数据做冷启动 SFT
2. 推理任务的 RL
3. 拒绝采样 + SFT
4. 全场景 RL

## 关键启示

- **RL 可以替代部分 SFT**,大模型的推理能力可以通过 RL 涌现
- **奖励工程极其关键**: 规则奖励比奖励模型更稳定
- **蒸馏依然有效**: R1 蒸馏到 Qwen-32B 后效果惊艳

## 工程注意点

- GRPO 比 PPO 显存占用更低 (无需 Critic)
- 长 CoT 训练对 KV Cache 与上下文长度要求高
- Reward Hacking 是主要风险
