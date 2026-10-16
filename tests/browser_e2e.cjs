#!/usr/bin/env node
/* ============================================================================
 * 认知诊断仪表盘 —— 浏览器 E2E 与 HTTP 静态契约测试（测试先行，RED）
 * ----------------------------------------------------------------------------
 * 零 @playwright/test 依赖：只用 Node 自带 `node:assert/strict` + `require('playwright')`。
 * 应用运行仍零依赖；本文件与可选 devDependency 仅用于前端验收，不进生产。
 *
 * ── 启动 / 关闭被测服务（外部编排或本机终端）──────────────────────────────
 *   # 1) 建库（一次性，可复现；--force 显式重建）
 *   python3 -m src.seed /tmp/cdiag-e2e.db
 *   # 2) 起服务（默认 127.0.0.1；改端口在第二个位置参数）
 *   python3 -m src.server /tmp/cdiag-e2e.db 8000
 *   # 3) 跑测试（见下方变量）
 *   # 4) 关闭服务：在起服务的终端按 Ctrl-C
 *
 * ── 运行所需环境变量（本文件不硬编码任何机器路径）──────────────────────────
 *   NODE_PATH=<含 playwright 的 node_modules 绝对路径>     # require('playwright') 解析
 *   PLAYWRIGHT_BROWSERS_PATH=<浏览器二进制缓存目录>         # chromium.launch() 定位
 *   E2E_BASE_URL=http://127.0.0.1:8000                      # 被测服务基址（默认 127.0.0.1:8000）
 *   E2E_SCREENSHOT_DIR=docs/validation                      # 首次失败截图目录（默认 docs/validation）
 *
 *   例：
 *   NODE_PATH=$PW_NODE_MODULES PLAYWRIGHT_BROWSERS_PATH=$PW_BROWSERS \
 *     E2E_BASE_URL=http://127.0.0.1:8000 node tests/browser_e2e.cjs
 *
 *   仅跑 HTTP 静态部分（不需要浏览器/playwright）：
 *   E2E_BASE_URL=http://127.0.0.1:8000 node tests/browser_e2e.cjs --http-only
 *
 * ── 退出码 ────────────────────────────────────────────────────────────────
 *   0 = 全部通过；1 = 任一断言失败 / 浏览器不可用 / 服务不可达。
 *
 * ── 前端契约（data-testid / 属性；本测试即冻结此契约，实现须遵循）─────────
 *   详见 docs/FRONTEND_CONTRACT.md。要点：
 *   [data-testid="student-select"]      <select>，<label for> 关联，12 个 <option>；默认选中 id=1
 *   [data-testid="current-student"]     当前学生名称
 *   [data-testid="radar-chart"]         <svg role="img" aria-label>；data-values="p1,…,p5"（KP1..KP5）；
 *                                       data-center="cx,cy"、data-radius="R"
 *   [data-testid="radar-polygon"]       <polygon points="x1,y1 … x5,y5">（5 顶点，KP1..KP5）
 *   [data-testid="mastery-table"]       <table>，5 行 [data-testid="mastery-row" data-kp-id="1..5"]
 *   [data-testid="mastery-value"]        掌握概率单元格，data-value=原始概率
 *   [data-testid="correct-rate-value"]   答对率单元格，data-value=原始答对率；表头含「答对率」+「对照」
 *   [data-testid="knowledge-graph"]     <svg role="img">，5 节点 5 有向边
 *   [data-testid="graph-node" data-kp-id data-value]         节点，可见文本含名称与 %
 *   [data-testid="graph-edge" data-parent data-child marker-end="url(#id)"]  前置→后续箭头，marker 须存在
 *   [data-testid="all-students-table"] <table>，60 个 [data-testid="matrix-cell"
 *                                       data-student-id data-kp-id data-value]（12×5 唯一对）
 *   [data-testid="limitations"]         合成小样本提示（含「合成」「小样本」）
 *   [data-testid="loading"]             加载态（含「加载」）
 *   [data-testid="error"] role="alert"  错误态（中文）
 *   [data-testid="retry"]               <button> 重试（文本「重试」）
 *   <meta name="viewport">              移动端适配
 *
 *   数值一致性：DOM 以 data-value 携带 API 原始浮点值，parseFloat 后以 1e-9 容差与
 *   真实 GET 接口逐项比对，不依赖展示格式；雷达再以几何（顶点距中心 ≈ R×概率）交叉验证。
 * ========================================================================== */

'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const N_STUDENTS = 12;
const N_KP = 5;
const N_EDGES = 5;
const EPS = 1e-9;

// ---------------------------------------------------------------------------
// 通用辅助
// ---------------------------------------------------------------------------

function close(a, b, tol = EPS) {
  return Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) < tol;
}

function timeout(ms, msg) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error(msg)), ms));
}

async function getJSON(baseURL, p) {
  const res = await fetch(baseURL + p);
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    /* 非 JSON 响应 */
  }
  return { status: res.status, headers: res.headers, text, json };
}

// 把 data-values 逗号串解析为浮点数组并逐项比对期望值。
function assertDataValues(dataValues, expected, label) {
  assert.ok(typeof dataValues === 'string' && dataValues.trim() !== '',
    `${label}: 缺少 data-values 属性`);
  const parts = dataValues.split(',').map((s) => s.trim());
  assert.strictEqual(parts.length, expected.length,
    `${label}: data-values 数量=${parts.length} 期望=${expected.length}`);
  parts.forEach((s, i) => {
    const v = parseFloat(s);
    assert.ok(Number.isFinite(v), `${label}[${i}]: 非有限值 "${s}"`);
    assert.ok(close(v, expected[i], 1e-9),
      `${label}[${i}]: 实际 ${v} 期望 ${expected[i]}`);
  });
}

// 等待页面数据完整：雷达 5 值 + 5 行概率表 + 5 图谱节点 + 当前学生均已渲染。
async function waitForReady(page) {
  await page.waitForFunction(() => {
    const radar = document.querySelector('[data-testid="radar-chart"]');
    if (!radar) return false;
    const dv = (radar.getAttribute('data-values') || '')
      .split(',').map((s) => s.trim()).filter(Boolean);
    if (dv.length !== 5) return false;
    if (document.querySelectorAll('[data-testid="mastery-row"]').length !== 5) return false;
    if (document.querySelectorAll('[data-testid="graph-node"]').length !== 5) return false;
    if (!document.querySelector('[data-testid="current-student"]')) return false;
    return true;
  }, undefined, { timeout: 15000 });
}

// 校验雷达实际几何：5 顶点距中心 ≈ radius × 概率（旋转无关，直接验证形状随值缩放）。
async function assertRadarGeometry(page, mastery) {
  const radar = page.locator('[data-testid="radar-chart"]');
  const centerStr = await radar.getAttribute('data-center');
  const radius = parseFloat(await radar.getAttribute('data-radius'));
  assert.ok(centerStr && /^-?[\d.eE+]+,-?[\d.eE+]+$/.test(centerStr),
    `雷达缺少 data-center="cx,cy"：${centerStr}`);
  const [cx, cy] = centerStr.split(',').map(parseFloat);
  assert.ok(Number.isFinite(radius) && radius > 0, `雷达 data-radius 非法：${radius}`);

  const pointsStr = await page.locator('[data-testid="radar-polygon"]').getAttribute('points');
  assert.ok(pointsStr, '缺少 radar-polygon');
  const pts = pointsStr.trim().split(/\s+/).map((p) => p.split(',').map(parseFloat));
  assert.strictEqual(pts.length, mastery.length, `雷达顶点数=${pts.length} 期望=${mastery.length}`);
  pts.forEach(([x, y], i) => {
    assert.ok(Number.isFinite(x) && Number.isFinite(y), `雷达顶点 ${i} 非有限坐标`);
    const d = Math.hypot(x - cx, y - cy);
    assert.ok(Math.abs(d - radius * mastery[i]) < 0.5,
      `雷达顶点 ${i} 距中心 ${d.toFixed(2)} 应≈ ${(radius * mastery[i]).toFixed(2)}（R=${radius}, v=${mastery[i]}）`);
  });
}

// 断言页面当前完整展示某学生（名称/雷达数值+几何/概率表/图谱节点），名称取自真实 API。
async function assertStudentShown(page, baseURL, sid) {
  const detail = await getJSON(baseURL, `/api/students/${sid}`);
  assert.strictEqual(detail.status, 200, `GET /api/students/${sid} → ${detail.status}`);
  const mastery = detail.json.mastery.map((m) => m.prob);
  const rate = detail.json.correct_rate.map((r) => r.rate);
  const names = detail.json.mastery.map((m) => m.name);
  const studentName = detail.json.student.name;

  const current = await page.locator('[data-testid="current-student"]').innerText();
  assert.ok(current.includes(studentName),
    `当前学生应为「${studentName}」，实为「${current}」`);

  assertDataValues(
    await page.locator('[data-testid="radar-chart"]').getAttribute('data-values'),
    mastery, '雷达 data-values');
  await assertRadarGeometry(page, mastery);

  const rows = page.locator('[data-testid="mastery-row"]');
  assert.strictEqual(await rows.count(), N_KP, '掌握概率表行数 != 5');
  const kpIds = [];
  for (let i = 0; i < N_KP; i++) {
    kpIds.push(parseInt(await rows.nth(i).getAttribute('data-kp-id'), 10));
  }
  assert.deepStrictEqual(kpIds.slice().sort(), [1, 2, 3, 4, 5],
    '掌握概率表 data-kp-id 应覆盖 KP1..KP5');

  for (let i = 0; i < N_KP; i++) {
    const row = rows.nth(i);
    const kpId = parseInt(await row.getAttribute('data-kp-id'), 10);
    const rowText = await row.innerText();
    assert.ok(rowText.includes(names[kpId - 1]),
      `第 ${i} 行缺少知识点名「${names[kpId - 1]}」`);
    const mv = parseFloat(await row.locator('[data-testid="mastery-value"]').getAttribute('data-value'));
    assert.ok(close(mv, mastery[kpId - 1], 1e-9),
      `KP${kpId} 掌握概率 UI=${mv} API=${mastery[kpId - 1]}`);
    const rv = parseFloat(await row.locator('[data-testid="correct-rate-value"]').getAttribute('data-value'));
    assert.ok(close(rv, rate[kpId - 1], 1e-9),
      `KP${kpId} 答对率 UI=${rv} API=${rate[kpId - 1]}`);
  }

  const nodes = page.locator('[data-testid="graph-node"]');
  assert.strictEqual(await nodes.count(), N_KP, '图谱节点数 != 5');
  for (let i = 0; i < N_KP; i++) {
    const kpId = parseInt(await nodes.nth(i).getAttribute('data-kp-id'), 10);
    const v = parseFloat(await nodes.nth(i).getAttribute('data-value'));
    assert.ok(close(v, mastery[kpId - 1], 1e-9),
      `图谱 KP${kpId} 节点 UI=${v} API=${mastery[kpId - 1]}`);
  }
}

// ---------------------------------------------------------------------------
// 阶段一：HTTP 静态 MIME / 编码 / 路径穿越（无需浏览器）
// ---------------------------------------------------------------------------

function httpStaticTests(baseURL) {
  const tests = [];

  tests.push({
    name: '静态 / → text/html; charset=utf-8 且 UTF-8 含中文',
    run: async () => {
      const r = await getJSON(baseURL, '/');
      assert.strictEqual(r.status, 200, `GET / → ${r.status}`);
      assert.strictEqual(r.headers.get('content-type'), 'text/html; charset=utf-8');
      assert.ok(r.text.includes('认知诊断'), '首页未包含中文标题「认知诊断」');
    },
  });

  tests.push({
    name: '静态 /index.html /style.css /app.js 各返回正确 MIME+charset',
    run: async () => {
      const expect = [
        ['/index.html', 'text/html; charset=utf-8'],
        ['/style.css', 'text/css; charset=utf-8'],
        ['/app.js', 'text/javascript; charset=utf-8'],
      ];
      for (const [p, mime] of expect) {
        const r = await getJSON(baseURL, p);
        assert.strictEqual(r.status, 200, `GET ${p} → ${r.status}`);
        assert.strictEqual(r.headers.get('content-type'), mime, `GET ${p} Content-Type`);
      }
    },
  });

  tests.push({
    name: '静态 /app.js 内容为 UTF-8 编码（无替换字符 U+FFFD）',
    run: async () => {
      const r = await getJSON(baseURL, '/app.js');
      assert.strictEqual(r.status, 200, `GET /app.js → ${r.status}`);
      assert.strictEqual(r.headers.get('content-type'), 'text/javascript; charset=utf-8');
      assert.ok(!r.text.includes('�'), '/app.js UTF-8 解码出现替换字符');
    },
  });

  tests.push({
    name: '路径穿越（裸 / 编码 / 反斜杠）一律 404 且不泄漏源码或库内容',
    run: async () => {
      const attempts = [
        '/../diagnosis.db',
        '/..%2Fdiagnosis.db',
        '/%2e%2e/diagnosis.db',
        '/..%5Cdiagnosis.db',
        '/static/../src/server.py',
        '/app.js/../../src/db.py',
      ];
      for (const p of attempts) {
        const r = await getJSON(baseURL, p);
        assert.strictEqual(r.status, 404, `GET ${p} → ${r.status}（应 404）`);
        assert.strictEqual(r.headers.get('content-type'),
          'application/json; charset=utf-8', `GET ${p} 应为 JSON 错误`);
        assert.ok(r.json && r.json.error && r.json.error.code === 'NOT_FOUND',
          `GET ${p} 错误体缺失 NOT_FOUND`);
        assert.ok(!r.text.includes('CREATE TABLE') && !r.text.includes('def '),
          `GET ${p} 泄漏了库/源码内容`);
      }
    },
  });

  tests.push({
    name: '未知静态路径 → 404 JSON（白名单路由，不落到文件系统）',
    run: async () => {
      const r = await getJSON(baseURL, '/nope.js');
      assert.strictEqual(r.status, 404, `GET /nope.js → ${r.status}`);
      assert.ok(r.json && r.json.error && r.json.error.code === 'NOT_FOUND');
    },
  });

  tests.push({
    name: '/api/* 保持 application/json（静态 MIME 不误用于 API）',
    run: async () => {
      const r = await getJSON(baseURL, '/api/meta');
      assert.strictEqual(r.status, 200, `GET /api/meta → ${r.status}`);
      assert.strictEqual(r.headers.get('content-type'), 'application/json; charset=utf-8');
    },
  });

  return tests;
}

// ---------------------------------------------------------------------------
// 阶段二：浏览器 E2E（7 组）
// ---------------------------------------------------------------------------

function browserTests(baseURL) {
  const tests = [];

  // B1 —— 首屏加载 / 12 名学生（名称取自真实 API）/ 语义骨架
  tests.push({
    name: 'B1 首屏加载：标题、12 名学生(与 API 一致)、默认学生、label、viewport、小样本提示',
    run: async ({ page }) => {
      const students = (await getJSON(baseURL, '/api/students')).json.students;
      assert.strictEqual(students.length, N_STUDENTS);

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const select = page.locator('[data-testid="student-select"]');
      await select.waitFor({ state: 'attached', timeout: 10000 });
      // 等待 12 个有效选项真正就绪（避免 attached 后选项尚未注入的竞态）
      await page.waitForFunction(() => {
        const s = document.querySelector('[data-testid="student-select"]');
        return !!s && s.options && s.options.length === 12;
      }, undefined, { timeout: 10000 });

      assert.ok((await page.title()).includes('认知诊断'),
        `页面标题缺少「认知诊断」：${await page.title()}`);

      const options = page.locator('[data-testid="student-select"] option');
      assert.strictEqual(await options.count(), N_STUDENTS, '学生选项数 != 12');
      const vals = await options.evaluateAll((els) => els.map((e) => e.value));
      const texts = await options.evaluateAll((els) => els.map((e) => e.textContent.trim()));
      students.forEach((s, i) => {
        assert.strictEqual(vals[i], String(s.id), `选项 ${i} value 应为 ${s.id}`);
        assert.strictEqual(texts[i], s.name, `选项 ${i} 文本应为 ${s.name}，实为 "${texts[i]}"`);
      });

      // 默认选中第一个学生（契约）
      assert.strictEqual(await select.inputValue(), '1', '默认应选中第一个学生（id=1）');

      const labelCount = await select.evaluate((el) => el.labels.length);
      assert.ok(labelCount >= 1, 'student-select 缺少关联 <label>');

      const viewportMeta = await page.locator('meta[name="viewport"]').count();
      assert.ok(viewportMeta >= 1, '缺少 <meta name="viewport">');

      const lim = page.locator('[data-testid="limitations"]');
      await lim.waitFor({ state: 'attached' });
      const limText = await lim.innerText();
      assert.ok(limText.includes('小样本'), '局限提示缺少「小样本」');
      assert.ok(limText.includes('合成'), '局限提示缺少「合成」');
    },
  });

  // B2 —— 所选学生数值/雷达几何与 API 一致，答对率标注对照
  tests.push({
    name: 'B2 所选学生：掌握概率/答对率/雷达几何逐项等于 API，答对率标注「对照」',
    run: async ({ page }) => {
      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const select = page.locator('[data-testid="student-select"]');
      await select.waitFor();
      await waitForReady(page);

      const sid = await select.inputValue();
      const detail = await getJSON(baseURL, `/api/students/${sid}`);
      assert.strictEqual(detail.status, 200);

      // 雷达语义
      const radar = page.locator('[data-testid="radar-chart"]');
      assert.strictEqual(await radar.getAttribute('role'), 'img', '雷达图缺少 role="img"');
      assert.ok(((await radar.getAttribute('aria-label')) || '').trim().length > 0,
        '雷达图缺少非空 aria-label');

      // 答对率标注对照
      const headText = await page.locator('[data-testid="mastery-table"]').first().innerText();
      assert.ok(headText.includes('答对率'), '表头缺少「答对率」');
      assert.ok(headText.includes('对照'), '答对率未标注「对照」（仅作对照，非掌握概率）');

      await assertStudentShown(page, baseURL, parseInt(sid, 10));
    },
  });

  // B3 —— 切换 + 快速切换无旧请求覆盖（确定时序，无固定睡眠）
  tests.push({
    name: 'B3 切换学生生效；旧请求晚返回不覆盖新选择',
    run: async ({ page }) => {
      let resolveHeld;
      const held = new Promise((r) => { resolveHeld = r; });
      let releaseHeld;
      let holdActive = true;

      // 提前注册「学生 1 详情已落定」信号（响应到达或被中止），
      // 以免 AbortController 在 selectOption 时立即触发 requestfailed、早于后续监听。
      let oldSettled = false;
      const settled = new Promise((resolve) => {
        const done = () => { if (!oldSettled) { oldSettled = true; resolve(); } };
        page.on('requestfailed', (req) => {
          if (/\/api\/students\/1$/.test(req.url())) done();
        });
        page.on('response', (resp) => {
          if (/\/api\/students\/1$/.test(resp.url())) done();
        });
      });

      // 拦截学生 1 的详情：先挂起（确认已发出），待释放后再继续。
      await page.route('**/api/students/*', async (route) => {
        const m = route.request().url().match(/\/(\d+)$/);
        if (m && m[1] === '1' && holdActive) {
          resolveHeld();
          await new Promise((r) => { releaseHeld = r; });
          try {
            await route.continue();
          } catch {
            /* 前端用 AbortController 取消时，请求已被浏览器中止，属正确结果 */
          }
        } else {
          await route.continue();
        }
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await page.locator('[data-testid="student-select"]').waitFor();
      await Promise.race([held, timeout(10000, '学生 1 详情请求未被拦截（默认学生契约被破坏）')]);

      // 切到学生 2：其详情立即通过；学生 1 或仍被挂起（token-guard）或已被中止（AbortController）。
      const select = page.locator('[data-testid="student-select"]');
      await select.selectOption('2');
      await waitForReady(page);
      await assertStudentShown(page, baseURL, 2);

      // 释放旧请求，等待其真正落定后（响应到达或中止），再判最终态。
      holdActive = false;
      releaseHeld();
      await Promise.race([settled, timeout(10000, '学生 1 旧请求未在预期时间内落定')]);
      // 让可能的错误覆盖在渲染帧内落地后再断言
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));

      await assertStudentShown(page, baseURL, 2);
      await page.unroute('**/api/students/*');
    },
  });

  // B4 —— 图谱 5 节点 5 有向边正确，箭头 marker 存在，节点文本用 textContent
  tests.push({
    name: 'B4 图谱：5 节点 5 箭头，与 /api/graph 一致，marker-end 引用存在的 marker',
    run: async ({ page }) => {
      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const svg = page.locator('[data-testid="knowledge-graph"]');
      await svg.waitFor();
      await waitForReady(page);

      const graph = await getJSON(baseURL, '/api/graph');
      const apiNodes = graph.json.nodes; // [{id,code,name}]
      const apiEdges = graph.json.edges; // [{parent,child}]
      assert.strictEqual(apiNodes.length, N_KP);
      assert.strictEqual(apiEdges.length, N_EDGES);

      const nodes = page.locator('[data-testid="graph-node"]');
      assert.strictEqual(await nodes.count(), N_KP, '图谱节点数 != 5');
      for (const n of apiNodes) {
        const node = page.locator(`[data-testid="graph-node"][data-kp-id="${n.id}"]`);
        assert.strictEqual(await node.count(), 1, `缺少图谱节点 KP${n.id}`);
        const text = await node.textContent(); // SVG <g> 文本用 textContent
        assert.ok(text.includes(n.name), `KP${n.id} 节点缺少名称「${n.name}」`);
        assert.ok(text.includes('%'), `KP${n.id} 节点未显示百分比`);
      }

      const edges = page.locator('[data-testid="graph-edge"]');
      assert.strictEqual(await edges.count(), N_EDGES, '图谱边数 != 5');
      const markerIds = await svg.locator('marker').evaluateAll((els) => els.map((e) => e.id));
      const gotEdges = [];
      for (let i = 0; i < N_EDGES; i++) {
        const e = edges.nth(i);
        const parent = parseInt(await e.getAttribute('data-parent'), 10);
        const child = parseInt(await e.getAttribute('data-child'), 10);
        const marker = await e.getAttribute('marker-end');
        assert.ok(marker, `边 ${parent}→${child} 缺少 marker-end 箭头`);
        const mm = marker.match(/url\(#([^)]+)\)/);
        assert.ok(mm, `边 ${parent}→${child} marker-end 格式异常：${marker}`);
        assert.ok(markerIds.includes(mm[1]),
          `边 ${parent}→${child} 的 marker-end 引用不存在的 marker #${mm[1]}`);
        gotEdges.push(`${parent}->${child}`);
      }
      const apiEdgeSet = apiEdges.map((e) => `${e.parent}->${e.child}`).sort();
      assert.deepStrictEqual(gotEdges.slice().sort(), apiEdgeSet,
        '图谱边集合与 /api/graph 不一致');
    },
  });

  // B5 —— 全体 12×5 概率表（60 唯一对）+ 不泄漏 profile_id
  tests.push({
    name: 'B5 全体 12×5 表 60 个唯一(student_id,kp_id)逐格等于 /api/diagnosis，不泄漏 profile_id',
    run: async ({ page }) => {
      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const table = page.locator('[data-testid="all-students-table"]');
      await table.waitFor();

      const diag = await getJSON(baseURL, '/api/diagnosis');
      const map = new Map();
      for (const row of diag.json.matrix) {
        map.set(`${row.student_id}:${row.kp_id}`, row.prob);
      }
      assert.strictEqual(map.size, N_STUDENTS * N_KP, '/api/diagnosis 不是 12×5=60 唯一行');

      const cells = page.locator('[data-testid="matrix-cell"]');
      assert.strictEqual(await cells.count(), N_STUDENTS * N_KP, '全体表单元格数 != 60');
      const seen = new Set();
      for (let i = 0; i < N_STUDENTS * N_KP; i++) {
        const c = cells.nth(i);
        const sid = parseInt(await c.getAttribute('data-student-id'), 10);
        const kid = parseInt(await c.getAttribute('data-kp-id'), 10);
        const key = `${sid}:${kid}`;
        assert.ok(!seen.has(key), `全体表出现重复 (${sid},${kid})`);
        seen.add(key);
        const expected = map.get(key);
        assert.ok(expected !== undefined, `全体表出现未知 (${sid},${kid})`);
        const v = parseFloat(await c.getAttribute('data-value'));
        assert.ok(close(v, expected, 1e-9),
          `全体表 (${sid},${kid}) UI=${v} API=${expected}`);
      }
      assert.strictEqual(seen.size, N_STUDENTS * N_KP, '全体表唯一对不足 60');

      const html = await page.content();
      assert.ok(!html.includes('profile_id'), '页面 HTML 泄漏 profile_id');
      for (const p of ['/api/students', '/api/students/1', '/api/diagnosis']) {
        const r = await getJSON(baseURL, p);
        assert.ok(!r.text.includes('profile_id'), `${p} 响应泄漏 profile_id`);
      }
    },
  });

  // B6 —— 中文加载态 / 网络失败中文错误与重试 / 恢复
  tests.push({
    name: 'B6 加载态、网络失败显示中文错误与「重试」并可恢复',
    run: async ({ page, expectFail, clearExpectFail }) => {
      // 请求屏障：挂起学生列表，确定性冻结加载态，验证中文提示后释放。
      let releaseList;
      const gate = new Promise((r) => { releaseList = r; });
      await page.route('**/api/students', async (route) => {
        await gate;
        await route.continue();
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const loading = page.locator('[data-testid="loading"]');
      await loading.waitFor({ state: 'visible', timeout: 5000 }); // 屏障下必然可见
      assert.ok((await loading.innerText()).includes('加载'),
        '加载态应为中文「加载」');
      releaseList();
      await page.locator('[data-testid="student-select"]').waitFor({ timeout: 10000 });
      await page.unroute('**/api/students');

      // 模拟网络失败：切学生 3 时详情请求被中止（豁免该注入的 net::ERR_FAILED）。
      await page.route('**/api/students/3', (route) => route.abort('failed'));
      expectFail(baseURL + '/api/students/3');
      await page.locator('[data-testid="student-select"]').selectOption('3');

      const error = page.locator('[data-testid="error"]');
      await error.waitFor({ state: 'visible', timeout: 5000 });
      assert.strictEqual(await error.getAttribute('role'), 'alert', '错误态缺少 role="alert"');
      assert.ok(/[一-鿿]/.test(await error.innerText()), '错误信息非中文');
      clearExpectFail(); // 已确认失败被消费，恢复 console.error 零容忍

      const retry = page.locator('[data-testid="retry"]');
      await retry.waitFor();
      assert.ok((await retry.innerText()).includes('重试'), '重试按钮文本非「重试」');

      // 恢复网络后点重试：错误态不可见（允许仍在 DOM 但隐藏），学生 3 数值实际更新。
      await page.unroute('**/api/students/3');
      await retry.click();
      await error.waitFor({ state: 'hidden', timeout: 5000 });

      const detail3 = await getJSON(baseURL, '/api/students/3');
      const mastery3 = detail3.json.mastery.map((m) => m.prob);
      await page.waitForFunction((exp) => {
        const r = document.querySelector('[data-testid="radar-chart"]');
        if (!r) return false;
        const dv = (r.getAttribute('data-values') || '').split(',').map((s) => parseFloat(s));
        return dv.length === exp.length && dv.every((v, i) => Math.abs(v - exp[i]) < 1e-9);
      }, mastery3, { timeout: 5000 });
      await assertStudentShown(page, baseURL, 3);
    },
  });

  // B7 —— 手机布局（390px 无横向溢出、5 节点完整可见）+ 键盘选择与可见焦点
  tests.push({
    name: 'B7 390px 无横向溢出、5 节点完整可见、键盘选择学生 12、焦点可见',
    run: async ({ page }) => {
      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      const select = page.locator('[data-testid="student-select"]');
      await select.waitFor();
      await waitForReady(page);

      const overflow = await page.evaluate(() => ({
        inner: window.innerWidth,
        doc: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
      }));
      assert.ok(overflow.inner <= 390, `视口宽 ${overflow.inner} 未按 390 设定`);
      assert.ok(overflow.doc <= 390, `documentElement 横向溢出：scrollWidth=${overflow.doc}`);
      assert.ok(overflow.body <= 390, `body 横向溢出：scrollWidth=${overflow.body}`);

      // 5 图谱节点完整可见（不越出 390px 横向视口）
      const graph = page.locator('[data-testid="knowledge-graph"]');
      await graph.scrollIntoViewIfNeeded();
      const nodes = page.locator('[data-testid="graph-node"]');
      assert.strictEqual(await nodes.count(), N_KP);
      for (let i = 0; i < N_KP; i++) {
        const node = nodes.nth(i);
        assert.ok(await node.isVisible(), `图谱节点 ${i} 不可见`);
        const box = await node.boundingBox();
        assert.ok(box && box.width > 0 && box.height > 0, `图谱节点 ${i} 无有效包围盒`);
        assert.ok(box.x >= 0 && box.x + box.width <= 390,
          `图谱节点 ${i} 横向越界：x=${box.x} width=${box.width}`);
      }

      // 键盘可达 + 可见焦点
      await select.focus();
      const focused = await page.evaluate(() =>
        document.activeElement && document.activeElement.getAttribute('data-testid'));
      assert.strictEqual(focused, 'student-select', 'select 未能获得键盘焦点');
      const focusStyle = await select.evaluate((el) => {
        const cs = getComputedStyle(el);
        return { outline: cs.outlineStyle, shadow: cs.boxShadow };
      });
      assert.ok(focusStyle.outline !== 'none' || focusStyle.shadow !== 'none',
        'select 聚焦无可见焦点指示（outline 与 box-shadow 均为 none）');

      // 键盘选择到学生 12，并等待其数值实际更新
      await page.keyboard.press('End');
      assert.strictEqual(await select.inputValue(), '12', '键盘 End 应选中学生 12');
      const d12 = await getJSON(baseURL, '/api/students/12');
      const mastery12 = d12.json.mastery.map((m) => m.prob);
      await page.waitForFunction((exp) => {
        const r = document.querySelector('[data-testid="radar-chart"]');
        if (!r) return false;
        const dv = (r.getAttribute('data-values') || '').split(',').map((s) => parseFloat(s));
        return dv.length === exp.length && dv.every((v, i) => Math.abs(v - exp[i]) < 1e-9);
      }, mastery12, { timeout: 5000 });
      await assertStudentShown(page, baseURL, 12);
    },
  });

  return tests;
}

// ---------------------------------------------------------------------------
// 运行器
// ---------------------------------------------------------------------------

// 为每个用例新建页面，并收集未处理 JS 错误（pageerror 零容忍；console.error 仅豁免注入的网络失败）。
async function newPage(context) {
  const page = await context.newPage();
  const jsErrors = [];
  const expectFailUrls = new Set();
  page.on('pageerror', (e) => jsErrors.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const text = m.text();
    // 豁免：测试显式声明预期失败时，注入的 route.abort 会触发 Chromium 的
    // 「Failed to load resource: net::ERR_FAILED」资源错误，并非应用未处理错误。
    if (expectFailUrls.size > 0 && /Failed to load resource|net::ERR_FAILED/i.test(text)) {
      return;
    }
    jsErrors.push(`console.error: ${text}`);
  });
  return {
    page,
    jsErrors,
    expectFail: (url) => expectFailUrls.add(url),
    clearExpectFail: () => expectFailUrls.clear(),
    close: () => page.close(),
  };
}

async function runBrowserCase(t, ctx) {
  try {
    await t.run(ctx);
    assert.deepStrictEqual(ctx.jsErrors, [],
      `未处理 JS 错误：${ctx.jsErrors.join(' | ')}`);
    process.stdout.write(`  ✔ ${t.name}\n`);
    return { name: t.name, ok: true };
  } catch (e) {
    process.stdout.write(`  ✘ ${t.name}\n      ${e.message.split('\n')[0]}\n`);
    return { name: t.name, ok: false, error: e };
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const httpOnly = argv.includes('--http-only');
  const screenshotDir = process.env.E2E_SCREENSHOT_DIR || 'docs/validation';
  const baseURL = (process.env.E2E_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

  const all = [];
  let failed = 0;

  console.log(`被测服务：${baseURL}`);
  console.log('\n── HTTP 静态 MIME / 编码 / 路径穿越 ──');
  for (const t of httpStaticTests(baseURL)) {
    try {
      await t.run();
      all.push({ name: t.name, ok: true });
      console.log(`  ✔ ${t.name}`);
    } catch (e) {
      all.push({ name: t.name, ok: false, error: e });
      failed += 1;
      console.log(`  ✘ ${t.name}\n      ${e.message.split('\n')[0]}`);
    }
  }

  if (!httpOnly) {
    console.log('\n── 浏览器 E2E（playwright）──');
    let browser;
    try {
      const { chromium } = require('playwright');
      browser = await chromium.launch({ headless: true });
      const bt = browserTests(baseURL);

      // 桌面视口（B1–B6）
      const desktop = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      for (const t of bt.slice(0, 6)) {
        const ctx = await newPage(desktop);
        let shotTaken = false;
        try {
          const r = await runBrowserCase(t, ctx);
          all.push(r);
          if (!r.ok) { failed += 1; shotTaken = true; }
        } finally {
          if (shotTaken) {
            const shot = path.join(screenshotDir, 'frontend-red-failure.png');
            try {
              fs.mkdirSync(screenshotDir, { recursive: true });
              await ctx.page.screenshot({ path: shot, fullPage: true }).catch(() => {});
            } catch { /* 截图失败不掩盖主错误 */ }
          }
          await ctx.close().catch(() => {});
        }
      }
      await desktop.close().catch(() => {});

      // 移动视口（B7，390px）
      const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const ctx = await newPage(mobile);
      const r = await runBrowserCase(bt[6], ctx);
      all.push(r);
      if (!r.ok) failed += 1;
      await ctx.close().catch(() => {});
      await mobile.close().catch(() => {});

      await browser.close().catch(() => {});
    } catch (e) {
      failed += 1;
      const reason = `浏览器不可用/未启动：${e.message.split('\n')[0]}`;
      all.push({ name: '浏览器 E2E（整体）', ok: false, error: new Error(reason) });
      console.log(`  ✘ ${reason}`);
      console.log('      （若为沙箱阻止 Chromium 进程注册，请由外部编排以同一命令运行并回填真实输出）');
    }
  }

  console.log('\n──────────────────────────────');
  const pass = all.filter((r) => r.ok).length;
  const fail = all.filter((r) => !r.ok).length;
  console.log(`结果：${pass} 通过 / ${fail} 失败（共 ${all.length} 项）`);
  if (fail > 0) {
    console.log('失败项：');
    for (const r of all.filter((x) => !x.ok)) {
      console.log(`  - ${r.name}\n    ${r.error && r.error.message ? r.error.message.split('\n')[0] : ''}`);
    }
  }
  console.log(`EXIT_CODE=${fail > 0 ? 1 : 0}`);
  process.exitCode = fail > 0 ? 1 : 0;
}

main().catch((e) => {
  console.error('运行器异常：', e);
  process.exitCode = 1;
});
