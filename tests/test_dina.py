"""src/dina.py 的算法 TDD 测试（RED 阶段：契约先行，实现未完成）。

按 docs/superpowers/specs/2026-10-16-cognitive-diagnosis-mvp-design.md §6 冻结的
数值契约编写。本文件只锁定接口与数学断言，不实现逻辑。

刻意不做两类断言：
- 不要求 12 名演示学生能精确恢复真实题参；
- 不断言所有后验都极端接近 0/1。
"""

import copy
import math
import unittest

from src.dina import FitResult, fit, posterior_marginal, posterior_profile


def _allclose(a, b, tol=1e-9):
    """无第三方依赖的近似比较（支持标量与嵌套序列）。"""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return (len(a) == len(b)
            and all(_allclose(x, y, tol) for x, y in zip(a, b)))


class PosteriorProfileTests(unittest.TestCase):
    """纯后验推断函数的契约与手算断言。"""

    def test_k1_single_item_hand_calc(self):
        # K=1、guess=.2、slip=.1、均匀先验下：
        #   答对 → P(掌握)=0.45/0.55=9/11；答错 → 0.05/0.45=1/9
        marg_c, ll_c = posterior_marginal([[1]], [[1]], [0.2], [0.1])
        self.assertAlmostEqual(marg_c[0][0], 9 / 11, places=12)
        self.assertAlmostEqual(ll_c, math.log(0.55), places=12)

        marg_w, ll_w = posterior_marginal([[1]], [[0]], [0.2], [0.1])
        self.assertAlmostEqual(marg_w[0][0], 1 / 9, places=12)
        self.assertAlmostEqual(ll_w, math.log(0.45), places=12)

        post_c, _ = posterior_profile([[1]], [[1]], [0.2], [0.1])
        self.assertTrue(_allclose(post_c[0], [2 / 11, 9 / 11], 1e-12))

    def test_and_gate_multi_skill(self):
        # 一题需要 {KP1,KP2}，答对：两个技能的边际相等且被 And 门“稀释”。
        marg, _ = posterior_marginal([[1, 1]], [[1]], [0.2], [0.1])
        self.assertAlmostEqual(marg[0][0], 11 / 15, places=12)
        self.assertAlmostEqual(marg[0][1], 11 / 15, places=12)
        self.assertLess(marg[0][0], 9 / 11)  # 比单技能题的证据更弱

        post, _ = posterior_profile([[1, 1]], [[1]], [0.2], [0.1])
        # 画像 00/01/10/11 → η=0/0/0/1
        self.assertTrue(_allclose(post[0],
                                  [2 / 15, 2 / 15, 2 / 15, 3 / 5], 1e-12))

    def test_marginal_is_probability_not_map_profile(self):
        # 输出是每技能的概率边际（连续值），不是 0/1 的 MAP 画像。
        marg, _ = posterior_marginal([[1, 1]], [[1]], [0.2], [0.1])
        self.assertEqual(len(marg), 1)
        self.assertEqual(len(marg[0]), 2)
        for v in marg[0]:
            self.assertTrue(0.0 < v < 1.0)  # 严格在 (0,1)，非硬 0/1

    def test_profile_bit_order_matches_q_columns(self):
        # bit0 ↔ Q 列 0（KP1），bit1 ↔ Q 列 1（KP2）。
        marg0, _ = posterior_marginal([[1, 0]], [[1]], [0.2], [0.1])
        self.assertAlmostEqual(marg0[0][0], 9 / 11, places=12)  # 有证据
        self.assertAlmostEqual(marg0[0][1], 0.5, places=12)     # 无证据 → 先验

        marg1, _ = posterior_marginal([[0, 1]], [[1]], [0.2], [0.1])
        self.assertAlmostEqual(marg1[0][0], 0.5, places=12)
        self.assertAlmostEqual(marg1[0][1], 9 / 11, places=12)

    def test_posterior_normalization(self):
        for q, x in (([[1]], [[1]]), ([[1]], [[0]]), ([[1, 1]], [[1]])):
            post, _ = posterior_profile(q, x, [0.2] * len(q), [0.1] * len(q))
            for row in post:
                self.assertAlmostEqual(sum(row), 1.0, places=12)

    def test_long_column_log_stability(self):
        # 800 题（400 对 400 错）：朴素连乘会下溢为 0/0=NaN，对数域应有限且正确。
        n = 800
        n_correct = 400
        g, s = 0.2, 0.1
        q = [[1]] * n
        x = [[1] * n_correct + [0] * (n - n_correct)]

        logp0 = n_correct * math.log(g) + (n - n_correct) * math.log(1 - g)
        logp1 = n_correct * math.log(1 - s) + (n - n_correct) * math.log(s)
        m = max(logp0, logp1)
        lse = m + math.log(math.exp(logp0 - m) + math.exp(logp1 - m))
        ref = math.exp(logp1 - lse)  # 均匀先验下的 P(α=1|X)

        marg, ll = posterior_marginal(q, x, [g] * n, [s] * n)
        self.assertTrue(math.isfinite(marg[0][0]) and marg[0][0] > 0.0)
        self.assertTrue(math.isfinite(ll))
        self.assertAlmostEqual(math.log(marg[0][0]), math.log(ref), places=6)

    def test_fixed_prior_default_uniform_and_respected(self):
        # 默认均匀先验 → 无证据技能边际 = 1/2。
        marg, _ = posterior_marginal([[1, 0]], [[1]], [0.2], [0.1])
        self.assertAlmostEqual(marg[0][1], 0.5, places=12)
        # 显式退化先验（质量全在 α=1）→ 即使答错，后验仍为 1。
        marg_d, _ = posterior_marginal([[1]], [[0]], [0.2], [0.1],
                                       prior=[0.0, 1.0])
        self.assertAlmostEqual(marg_d[0][0], 1.0, places=12)

    def test_rejects_illegal_q_x_and_shapes(self):
        # Q/X 形状、二进制、空知识需求、题参长度/值域。
        cases = [
            (posterior_marginal, ([], [[1]], [0.2], [0.1])),          # 空 Q
            (posterior_marginal, ([[1]], [[1, 0]], [0.2], [0.1])),    # X 题数不匹配
            (posterior_marginal, ([[2]], [[1]], [0.2], [0.1])),       # Q 非 0/1
            (posterior_marginal, ([[1]], [[2]], [0.2], [0.1])),       # X 非 0/1
            (posterior_marginal, ([[0, 0]], [[1]], [0.2], [0.1])),    # 空知识需求
            (posterior_marginal, ([[1]], [[1]], [0.2, 0.2], [0.1])),  # guess 长度错
            (posterior_marginal, ([[1]], [[1]], [1.5], [0.1])),       # guess 越界
            (posterior_marginal, ([[1]], [[1]], [0.2], [-0.5])),      # slip 越界
        ]
        for func, args in cases:
            with self.assertRaises(ValueError, msg=repr(args)):
                func(*args)

    def test_does_not_modify_inputs(self):
        q = [[1, 0], [0, 1], [1, 1]]
        x = [[1, 1, 0], [0, 1, 1]]
        q0, x0 = copy.deepcopy(q), copy.deepcopy(x)
        posterior_marginal(q, x, [0.2, 0.2, 0.2], [0.1, 0.1, 0.1])
        self.assertEqual(q, q0)
        self.assertEqual(x, x0)

    def test_determinism_pure(self):
        q = [[1, 0], [0, 1], [1, 1]]
        x = [[1, 1, 0], [0, 1, 1], [1, 0, 0]]
        a = posterior_marginal(q, x, [0.2, 0.2, 0.2], [0.1, 0.1, 0.1])
        b = posterior_marginal(q, x, [0.2, 0.2, 0.2], [0.1, 0.1, 0.1])
        self.assertTrue(_allclose(a[0], b[0], 1e-12))
        self.assertAlmostEqual(a[1], b[1], places=12)

    def test_item_permutation_invariance_pure(self):
        q = [[1, 0], [0, 1], [1, 1]]
        x = [[1, 1, 0], [0, 1, 1]]
        g, s = [0.2, 0.15, 0.1], [0.1, 0.2, 0.05]
        perm = [2, 0, 1]
        qp = [q[i] for i in perm]
        xp = [[row[i] for i in perm] for row in x]
        gp = [g[i] for i in perm]
        sp = [s[i] for i in perm]
        a = posterior_marginal(q, x, g, s)
        b = posterior_marginal(qp, xp, gp, sp)
        self.assertTrue(_allclose(a[0], b[0], 1e-12))
        self.assertAlmostEqual(a[1], b[1], places=12)

    def test_skill_permutation_invariance_pure(self):
        # 交换 Q 列（技能顺序）→ 边际列相应交换。
        q = [[1, 0], [0, 1], [1, 1]]
        x = [[1, 1, 0], [0, 1, 1]]
        g, s = [0.2, 0.2, 0.2], [0.1, 0.1, 0.1]
        qs = [[row[1], row[0]] for row in q]
        a = posterior_marginal(q, x, g, s)
        b = posterior_marginal(qs, x, g, s)
        self.assertTrue(_allclose([a[0][s_i][0] for s_i in range(len(x))],
                                  [b[0][s_i][1] for s_i in range(len(x))], 1e-12))


class FitTests(unittest.TestCase):
    """EM 校准 fit() 的契约断言（小样本合成，不要求恢复真实题参）。"""

    Q = [[1, 0], [0, 1], [1, 1]]
    X = [[1, 1, 0], [0, 1, 1], [1, 0, 0]]

    def _fit(self, **kw):
        kw.setdefault("max_iter", 200)
        return fit(self.Q, self.X, **kw)

    def test_likelihood_non_decreasing(self):
        res = self._fit()
        hist = res.loglik_history
        self.assertGreaterEqual(len(hist), 2)
        for a, b in zip(hist, hist[1:]):
            self.assertGreaterEqual(b - a, -1e-8)  # 无实质下降

    def test_param_bounds(self):
        res = self._fit()
        for g in res.guess:
            self.assertTrue(0.02 <= g <= 0.35)
        for s in res.slip:
            self.assertTrue(0.02 <= s <= 0.35)

    def test_final_params_history_and_relik_consistent(self):
        res = self._fit()
        _, ll_relik = posterior_marginal(self.Q, self.X, res.guess, res.slip)
        self.assertAlmostEqual(res.loglik_history[-1], ll_relik, places=8)

    def test_max_iter_exhaustion_not_converged(self):
        res = self._fit(max_iter=1)
        self.assertFalse(res.converged)
        self.assertEqual(len(res.loglik_history), 2)  # [init, iter_1]

    def test_determinism_fit(self):
        a = self._fit()
        b = self._fit()
        self.assertTrue(_allclose(a.guess, b.guess, 1e-9))
        self.assertTrue(_allclose(a.slip, b.slip, 1e-9))
        self.assertTrue(_allclose(a.posterior_marginal, b.posterior_marginal, 1e-9))
        self.assertEqual(a.converged, b.converged)

    def test_fixed_prior_only_uniform(self):
        # fit 只接受固定均匀先验，不接受其它先验或类比例拟合。
        with self.assertRaises(ValueError):
            fit(self.Q, self.X, prior="estimated")
        # FitResult 不含类比例字段（先验不被拟合）。
        res = self._fit()
        self.assertIsInstance(res, FitResult)
        self.assertEqual(set(res._fields),
                         {"guess", "slip", "loglik_history",
                          "posterior_marginal", "converged"})

    def test_item_permutation_invariance_fit(self):
        perm = [2, 0, 1]
        qp = [self.Q[i] for i in perm]
        xp = [[row[i] for i in perm] for row in self.X]
        a = self._fit()
        b = fit(qp, xp, max_iter=200)
        self.assertTrue(_allclose(a.posterior_marginal, b.posterior_marginal, 1e-6))
        self.assertAlmostEqual(a.loglik_history[-1], b.loglik_history[-1], places=6)

    def test_skill_permutation_invariance_fit(self):
        qs = [[row[1], row[0]] for row in self.Q]
        a = self._fit()
        b = fit(qs, self.X, max_iter=200)
        a_m = a.posterior_marginal
        b_m = b.posterior_marginal
        for i in range(len(self.X)):
            self.assertAlmostEqual(a_m[i][0], b_m[i][1], places=6)
            self.assertAlmostEqual(a_m[i][1], b_m[i][0], places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
