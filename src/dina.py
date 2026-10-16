"""DINA 认知诊断模型 —— 接口桩（TDD RED 阶段，逻辑未实现）。

本文件只定义冻结的接口与契约（见
docs/superpowers/specs/2026-10-16-cognitive-diagnosis-mvp-design.md §6），
所有公开函数当前抛 NotImplementedError。实现留待 feat(GREEN) 阶段。

约定：
- Q：形状 (n_items, K)，元素 0/1，Q[i][k]=1 表示第 i 题需要掌握第 k 个知识点。
- X：形状 (n_students, n_items)，元素 0/1，X[s][i]=1 表示第 s 名学生答对第 i 题。
- guess / slip：长度 n_items 的序列（标量亦可，视为广播），元素 ∈ [0,1]。
- 画像索引 c ∈ [0, 2^K)：bit k 对应知识点 k（bit0 ↔ KP1），与 Q 列 k 对齐。
- prior：None 表示固定均匀先验 1/2^K；也可显式传长度 2^K 的概率向量。
"""

from typing import NamedTuple, Sequence


class FitResult(NamedTuple):
    """EM 校准结果。"""

    guess: Sequence[float]                      # 每题 guess（校准后）
    slip: Sequence[float]                       # 每题 slip（校准后）
    loglik_history: Sequence[float]             # [init, iter_1, ..., iter_T]
    posterior_marginal: Sequence[Sequence[float]]  # (n_students, K)
    converged: bool                             # max_iter 耗尽时为 False


def posterior_profile(Q, X, guess, slip, prior=None):
    """E 步：每名学生在 2^K 画像上的归一化后验 + 对数似然。

    返回 (posterior, loglik)：
    - posterior：形状 (n_students, 2^K)，每行和为 1（归一化）。
    - loglik：全体学生对数似然 log P(X)。
    """
    raise NotImplementedError


def posterior_marginal(Q, X, guess, slip, prior=None):
    """对数后验边际：P(α_k=1 | X_s)。

    返回 (marginal, loglik)：
    - marginal：形状 (n_students, K)，marginal[s][k] ∈ [0,1]。
    - loglik：全体学生对数似然 log P(X)。
    """
    raise NotImplementedError


def fit(Q, X, *, prior="uniform", guess_bounds=(0.02, 0.35),
        slip_bounds=(0.02, 0.35), init=(0.2, 0.1), max_iter=200, tol=1e-8):
    """EM 校准 guess/slip，返回 FitResult。

    锁定契约：
    - 先验固定均匀 1/2^K（prior 仅支持 "uniform"，不拟合类比例）。
    - guess/slip 校准后截断到 guess_bounds / slip_bounds（默认 [0.02, 0.35]）。
    - 初始 guess=init[0]=0.2、slip=init[1]=0.1；E 步对数域 logsumexp。
    - 停止（两步）：先拒绝超出浮点容差的显著负对数似然增量；再以增量 < tol 判收敛。
    - max_iter 耗尽时 converged=False；最终题参、历史末项、重算似然一致。
    """
    raise NotImplementedError
