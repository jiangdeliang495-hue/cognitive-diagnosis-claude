"""DINA 认知诊断模型（纯算法实现，标准库 + 零第三方依赖）。

契约见 docs/superpowers/specs/2026-10-16-cognitive-diagnosis-mvp-design.md §6。

约定：
- Q：形状 (n_items, K)，元素 0/1，Q[i][k]=1 表示第 i 题需要掌握第 k 个知识点。
- X：形状 (n_students, n_items)，元素 0/1，X[s][i]=1 表示第 s 名学生答对第 i 题。
- guess / slip：长度 n_items 的序列（标量亦可，广播），元素 ∈ [0,1]。
- 画像索引 c ∈ [0, 2^K)：bit k 对应知识点 k（bit0 ↔ KP1），与 Q 列 k 对齐。
- prior：None 表示固定均匀先验 1/2^K；也可显式传长度 2^K 的概率向量。

DINA 模型：
- 理想作答（And 门，非补偿）：η_cj = ∏_k α_{c,k}^{q_jk}，即画像 c 须掌握第 j 题
  Q 行要求的全部知识点，η 才为 1。
- 观测模型：P(X=1 | α_c) = (1-slip_j) 若 η=1，否则 guess_j。
"""

import math
from typing import NamedTuple, Sequence


class FitResult(NamedTuple):
    """EM 校准结果。"""

    guess: Sequence[float]                      # 每题 guess（校准后）
    slip: Sequence[float]                       # 每题 slip（校准后）
    loglik_history: Sequence[float]             # [init, iter_1, ..., iter_T]
    posterior_marginal: Sequence[Sequence[float]]  # (n_students, K)
    converged: bool                             # max_iter 耗尽时为 False


# ---------------------------------------------------------------------------
# 数值辅助
# ---------------------------------------------------------------------------

def _log(x):
    """安全对数：log(0) = -inf（避免 math.log(0) 抛异常）。"""
    return math.log(x) if x > 0.0 else -math.inf


def _logsumexp(logs):
    """对数域求和，稳定处理 -inf。"""
    m = max(logs)
    if m == -math.inf:
        return -math.inf
    return m + math.log(sum(math.exp(x - m) for x in logs))


# ---------------------------------------------------------------------------
# 输入验证
# ---------------------------------------------------------------------------

def _validate_q(Q):
    """验证 Q：非空、2D、0/1、每行至少一个 1（禁止空知识需求题）。

    返回 (n_items, K, required_masks)，required_masks[j] 为第 j 题所需技能的位掩码。
    """
    if not isinstance(Q, (list, tuple)) or len(Q) == 0:
        raise ValueError("Q 不能为空")
    K = None
    masks = []
    for i, row in enumerate(Q):
        if not isinstance(row, (list, tuple)) or len(row) == 0:
            raise ValueError("Q 第 %d 行不能为空" % i)
        if K is None:
            K = len(row)
        elif len(row) != K:
            raise ValueError("Q 行长度不一致")
        mask = 0
        for k, v in enumerate(row):
            if v not in (0, 1):
                raise ValueError("Q 元素必须为 0/1")
            if v == 1:
                mask |= 1 << k
        if mask == 0:
            raise ValueError("Q 第 %d 行无知识点需求（空知识需求题）" % i)
        masks.append(mask)
    return len(Q), K, masks


def _validate_x(X, n_items):
    """验证 X：非空、2D、0/1、列数与题数一致。返回 n_students。"""
    if not isinstance(X, (list, tuple)) or len(X) == 0:
        raise ValueError("X 不能为空")
    for si, row in enumerate(X):
        if not isinstance(row, (list, tuple)) or len(row) != n_items:
            raise ValueError("X 第 %d 行题数与 Q 不匹配" % si)
        for v in row:
            if v not in (0, 1):
                raise ValueError("X 元素必须为 0/1")
    return len(X)


def _normalize_params(param, n_items, name):
    """规范化 guess/slip：标量广播为长度 n_items 的序列；校验值域 [0,1]。"""
    if isinstance(param, (int, float)):
        vals = [float(param)] * n_items
    else:
        try:
            vals = [float(v) for v in param]
        except (TypeError, ValueError):
            raise ValueError("%s 必须为数值或数值序列" % name)
        if len(vals) != n_items:
            raise ValueError("%s 长度须等于题数 %d" % (name, n_items))
    for v in vals:
        if v < 0.0 or v > 1.0:
            raise ValueError("%s 必须在 [0,1] 内" % name)
    return vals


def _prior_log(prior, K):
    """固定先验的对数：None 为均匀 1/2^K；否则验证归一化概率向量。"""
    n = 1 << K
    if prior is None:
        return [-K * math.log(2.0)] * n
    try:
        vals = [float(v) for v in prior]
    except (TypeError, ValueError):
        raise ValueError("prior 必须为概率向量或 None")
    if len(vals) != n:
        raise ValueError("prior 长度须等于 2^K=%d" % n)
    if any(v < 0.0 for v in vals):
        raise ValueError("prior 不能含负值")
    if abs(sum(vals) - 1.0) > 1e-9:
        raise ValueError("prior 须归一化（和为 1）")
    return [_log(v) for v in vals]


# ---------------------------------------------------------------------------
# E 步 / 边际
# ---------------------------------------------------------------------------

def _posterior(Q, X, guess, slip, log_prior, n_items, K, n_students, masks):
    """E 步：每名学生在 2^K 画像上的归一化后验 + 总对数似然（对数域稳定）。"""
    n_profiles = 1 << K
    post = [[0.0] * n_profiles for _ in range(n_students)]
    ll_total = 0.0
    for si in range(n_students):
        logs = [0.0] * n_profiles
        for c in range(n_profiles):
            acc = log_prior[c]
            for j in range(n_items):
                eta = 1 if (c & masks[j]) == masks[j] else 0
                if eta:
                    lp = _log(1.0 - slip[j])   # P(X=1|全掌握)
                    lq = _log(slip[j])         # P(X=0|全掌握)
                else:
                    lp = _log(guess[j])        # P(X=1|未全掌握)
                    lq = _log(1.0 - guess[j])  # P(X=0|未全掌握)
                acc += lp if X[si][j] else lq
            logs[c] = acc
        lse = _logsumexp(logs)
        if lse == -math.inf:
            raise ValueError("给定参数下学生 %d 的似然数值下溢" % si)
        ll_total += lse
        row = post[si]
        for c in range(n_profiles):
            row[c] = math.exp(logs[c] - lse)
    return post, ll_total


def _marginalize(post, K, n_students):
    """从画像后验求每技能的知识边际 P(α_k=1)。"""
    n_profiles = 1 << K
    marginal = []
    for si in range(n_students):
        row = post[si]
        mrow = []
        for k in range(K):
            bit = 1 << k
            mrow.append(sum(row[c] for c in range(n_profiles) if c & bit))
        marginal.append(mrow)
    return marginal


def posterior_profile(Q, X, guess, slip, prior=None):
    """E 步：每名学生在 2^K 画像上的归一化后验 + 对数似然。

    返回 (posterior, loglik)：
    - posterior：形状 (n_students, 2^K)，每行和为 1（归一化）。
    - loglik：全体学生对数似然 log P(X)。
    """
    n_items, K, masks = _validate_q(Q)
    n_students = _validate_x(X, n_items)
    g = _normalize_params(guess, n_items, "guess")
    s = _normalize_params(slip, n_items, "slip")
    log_prior = _prior_log(prior, K)
    return _posterior(Q, X, g, s, log_prior, n_items, K, n_students, masks)


def posterior_marginal(Q, X, guess, slip, prior=None):
    """对数后验边际：P(α_k=1 | X_s)。

    返回 (marginal, loglik)：
    - marginal：形状 (n_students, K)，marginal[s][k] ∈ [0,1]。
    - loglik：全体学生对数似然 log P(X)。
    """
    n_items, K, masks = _validate_q(Q)
    n_students = _validate_x(X, n_items)
    g = _normalize_params(guess, n_items, "guess")
    s = _normalize_params(slip, n_items, "slip")
    log_prior = _prior_log(prior, K)
    post, ll = _posterior(Q, X, g, s, log_prior, n_items, K, n_students, masks)
    return _marginalize(post, K, n_students), ll


# ---------------------------------------------------------------------------
# EM 校准
# ---------------------------------------------------------------------------

def _mstep(Q, X, post, guess, slip, masks, gl, gu, sl, su,
           n_items, K, n_students):
    """M 步：期望计数更新 guess/slip，并精确截断到 [下界, 上界]；零分母保留旧值。"""
    n_profiles = 1 << K
    new_guess = list(guess)
    new_slip = list(slip)
    for j in range(n_items):
        mask = masks[j]
        n11 = n10 = n01 = n00 = 0.0
        for si in range(n_students):
            row = post[si]
            x = X[si][j]
            for c in range(n_profiles):
                w = row[c]
                if w == 0.0:
                    continue
                eta = 1 if (c & mask) == mask else 0
                if eta:
                    if x:
                        n11 += w
                    else:
                        n10 += w
                else:
                    if x:
                        n01 += w
                    else:
                        n00 += w
        d_slip = n11 + n10
        if d_slip > 0.0:
            new_slip[j] = min(su, max(sl, n10 / d_slip))
        d_guess = n01 + n00
        if d_guess > 0.0:
            new_guess[j] = min(gu, max(gl, n01 / d_guess))
    return new_guess, new_slip


def fit(Q, X, *, prior="uniform", guess_bounds=(0.02, 0.35),
        slip_bounds=(0.02, 0.35), init=(0.2, 0.1), max_iter=200, tol=1e-8):
    """EM 校准 guess/slip，返回 FitResult。

    锁定契约：
    - 先验固定均匀 1/2^K（prior 仅支持 "uniform"，不拟合类比例）。
    - guess/slip 校准后截断到 guess_bounds / slip_bounds（默认 [0.02, 0.35]）。
    - 初始 guess=init[0]、slip=init[1]；E 步对数域 logsumexp。
    - 停止（两步）：先拒绝超出浮点容差的显著负对数似然增量；再以增量 < tol 判收敛。
    - max_iter 耗尽时 converged=False；最终题参、历史末项、重算似然一致。
    """
    if prior != "uniform":
        raise ValueError("fit 仅支持固定均匀先验 'uniform'")
    if max_iter < 1:
        raise ValueError("max_iter 必须 >= 1")
    gl, gu = guess_bounds
    sl, su = slip_bounds
    if not (0.0 <= gl <= gu <= 1.0) or not (0.0 <= sl <= su <= 1.0):
        raise ValueError("题参边界非法")

    n_items, K, masks = _validate_q(Q)
    n_students = _validate_x(X, n_items)
    log_prior = [-K * math.log(2.0)] * (1 << K)

    guess = [float(init[0])] * n_items
    slip = [float(init[1])] * n_items
    post, ll_prev = _posterior(Q, X, guess, slip, log_prior,
                               n_items, K, n_students, masks)
    history = [ll_prev]
    converged = False

    for _ in range(max_iter):
        guess, slip = _mstep(Q, X, post, guess, slip, masks,
                             gl, gu, sl, su, n_items, K, n_students)
        post, ll_cur = _posterior(Q, X, guess, slip, log_prior,
                                  n_items, K, n_students, masks)
        history.append(ll_cur)
        delta = ll_cur - ll_prev
        if delta < -1e-9:
            raise ArithmeticError("EM 对数似然显著下降：delta=%.3e" % delta)
        if delta < tol:
            converged = True
            break
        ll_prev = ll_cur

    marginal = _marginalize(post, K, n_students)
    return FitResult(guess, slip, history, marginal, converged)
