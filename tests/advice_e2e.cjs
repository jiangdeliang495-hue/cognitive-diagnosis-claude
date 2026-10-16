#!/usr/bin/env node
/* ============================================================================
 * LLM 学习建议 —— 浏览器交互契约 E2E（测试先行，RED：UI 尚未实现）
 * ----------------------------------------------------------------------------
 * 与被测服务约定：
 *   1) 起服务（基础页面需要真实 GET 接口；建议相关路由全部由本文件 mock，
 *      并带兜底安全网：任何未被具体 mock 接管的付费 POST 一律 abort 并判违规，
 *      绝不意外打到真实 API）：
 *      python3 -m src.seed /tmp/cdiag-e2e.db
 *      python3 -m src.server /tmp/cdiag-e2e.db 8000 &
 *   2) 运行：
 *      NODE_PATH=<playwright node_modules> PLAYWRIGHT_BROWSERS_PATH=<pw-browsers> \
 *        E2E_BASE_URL=http://127.0.0.1:8000 node tests/advice_e2e.cjs
 *   退出码：0 = 全部通过；1 = 任一断言失败 / 浏览器不可用。
 *
 * 契约（data-testid；详见 docs/LLM_SUGGESTIONS.md §7）：
 *   [data-testid="advice-section"]        AI 学习建议区
 *   [data-testid="generate-advice"]       「生成学习建议」按钮（生成中 disabled；键盘可激活）
 *   [data-testid="advice-config-missing"] 未配置提示（中文，含「未配置」；可隐藏于空容器）
 *   [data-testid="advice-loading"]        独立加载态（中文）
 *   [data-testid="advice-error"]          独立错误（role="alert"，中文）
 *   [data-testid="advice-retry"]          重试按钮（文本「重试」）
 *   [data-testid="advice-content"]        建议内容（仅 textContent 渲染，禁 innerHTML）
 *   行为：详情成功后 GET /api/llm/status；configured=true 才显示按钮；仅点击才 POST；
 *   切学生清空建议并 abort 旧等待；同学生 ID 的旧请求按序号区分，最晚返回的旧响应
 *   绝不覆盖新建议；长英文单词须换行不产生 390px 横向溢出。
 *   错误豁免：仅对测试显式注入 URL 的预期资源错误豁免——按 console 消息
 *   location().url 与该 case 注入 URL 精确匹配、状态码为确切 5xx；注入记录
 *   保留至页面关闭（容忍故意失败的迟到日志）；location 缺失不泛化豁免；
 *   其余 pageerror 与非预期 console.error 仍零容忍。
 * ========================================================================== */

'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const SID_RE = /\/(\d+)\/advice$/;

function timeout(ms, msg) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error(msg)), ms));
}

function adviceBody(sid, marker, fields) {
  const f = fields || {};
  return JSON.stringify({
    student_id: sid,
    source: 'llm',
    provider: 'deepseek',
    model: 'deepseek-v4-pro',
    reasoning_effort: 'max',
    request_id: 'chatcmpl-mock',
    advice: {
      summary: f.summary !== undefined ? f.summary : marker + '：本周重点巩固薄弱知识点。',
      priorities: [
        {
          kp_id: 2,
          reason: f.reason !== undefined ? f.reason : '掌握概率较低，是加减的前置。',
          actions: f.actions !== undefined ? f.actions : ['每天练 5 道异分母通分题'],
          check: f.check !== undefined ? f.check : '独立完成 3 题全对',
        },
      ],
    },
  });
}

async function mockStatus(page, configured) {
  await page.route('**/api/llm/status', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(configured
      ? { configured: true, provider: 'deepseek', model: 'deepseek-v4-pro',
          reasoning_effort: 'max' }
      : { configured: false, provider: null, model: null, reasoning_effort: null }),
  }));
}

// 兜底安全网：先注册、后由具体 mock 覆盖；漏网的付费 POST 一律 abort 并记为违规
function installSafetyNet(page) {
  const unexpected = [];
  page.route('**/api/students/*/advice', (route) => {
    unexpected.push(route.request().url());
    route.abort('failed');
  });
  return unexpected;
}

// 等待基础诊断页数据完整
async function waitReady(page) {
  await page.waitForFunction(() => {
    const radar = document.querySelector('[data-testid="radar-chart"]');
    if (!radar) return false;
    const dv = (radar.getAttribute('data-values') || '')
      .split(',').map((s) => s.trim()).filter(Boolean);
    return dv.length === 5;
  }, undefined, { timeout: 15000 });
}

function browserTests(baseURL) {
  const tests = [];

  // C1 —— 首屏/切学生/刷新零自动 POST
  tests.push({
    name: 'C1 首屏/切学生/刷新不自动发付费 POST，configured 才显示按钮',
    run: async ({ page }) => {
      await mockStatus(page, true);
      let postCount = 0;
      await page.route('**/api/students/*/advice', (route) => {
        postCount += 1;
        const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
        route.fulfill({ status: 200, contentType: 'application/json',
                        body: adviceBody(sid, '建议') });
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);
      await page.locator('[data-testid="advice-section"]')
        .waitFor({ state: 'attached', timeout: 10000 });
      const btn = page.locator('[data-testid="generate-advice"]');
      await btn.waitFor({ state: 'visible', timeout: 10000 });
      assert.strictEqual(postCount, 0, '首屏不得自动发付费 POST');

      await page.locator('[data-testid="student-select"]').selectOption('2');
      await page.waitForTimeout(300); // 观察窗口：让可能存在的违规自动请求暴露
      assert.strictEqual(postCount, 0, '切学生不得自动发付费 POST');
      const content = page.locator('[data-testid="advice-content"]');
      const txt = (await content.innerText().catch(() => '')).trim();
      const hidden = await content.isHidden().catch(() => true);
      assert.ok(txt === '' || hidden, '切学生后建议应立即清空');

      await page.reload({ waitUntil: 'domcontentloaded' });
      await waitReady(page);
      await page.waitForTimeout(300);
      assert.strictEqual(postCount, 0, '刷新不得自动发付费 POST');
    },
  });

  // C2 —— 真实 POST 方法/JSON Content-Type/严格 {}；生成中禁用；各文本字段防 XSS
  tests.push({
    name: 'C2 POST 方法/JSON 体/严格{}核对；生成中禁用；各字段字面 HTML 不执行',
    run: async ({ page }) => {
      await mockStatus(page, true);
      let releaseGate;
      const gate = new Promise((r) => { releaseGate = r; });
      const posts = [];
      let firstCapturedResolve;
      const firstCaptured = new Promise((r) => { firstCapturedResolve = r; });
      let firstDone = false;
      await page.route('**/api/students/*/advice', async (route) => {
        posts.push({
          url: route.request().url(),
          method: route.request().method(),
          contentType: (route.request().headers()['content-type'] || ''),
          data: route.request().postData(),
        });
        if (!firstDone) { firstDone = true; firstCapturedResolve(); }
        await gate; // 挂起，观察生成中的禁用与加载态
        const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
        await route.fulfill({
          status: 200, contentType: 'application/json',
          body: adviceBody(sid, 'XSS<img src=x onerror=window.__xss=1>', {
            reason: '<b>reason</b>', actions: ['<script>window.__xss=1</script>动作'],
            check: '<img src=x onerror=window.__xss=1>',
          }),
        });
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);
      const btn = page.locator('[data-testid="generate-advice"]');
      await btn.waitFor({ state: 'visible' });
      assert.strictEqual(posts.length, 0);
      await btn.click();
      // 确定时序：等待请求被精确捕获后再断言，避免异步 route 竞态
      await Promise.race([firstCaptured, timeout(5000, 'POST 未被捕获')]);
      assert.strictEqual(posts.length, 1, '点击应恰好发一次 POST');
      assert.strictEqual(posts[0].method, 'POST');
      assert.ok(posts[0].contentType.includes('application/json'),
        `Content-Type 应为 application/json，实为 ${posts[0].contentType}`);
      assert.deepStrictEqual(JSON.parse(posts[0].data), {}, '请求体必须严格 {}');
      assert.ok(posts[0].url.split('?')[0].endsWith('/api/students/1/advice'));

      assert.ok(await btn.isDisabled(), '生成中按钮必须禁用（防连点）');
      await page.locator('[data-testid="advice-loading"]')
        .waitFor({ state: 'visible', timeout: 5000 });
      assert.strictEqual(await page.locator('[data-testid="radar-chart"]').count(), 1,
        '建议加载不得影响诊断区');

      releaseGate();
      // 等待预期 summary/reason/actions/check 文本实际出现
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        if (!el) return false;
        const t = el.textContent;
        return t.includes('XSS<img') && t.includes('reason') &&
          t.includes('动作') && t.includes('src=x');
      }, undefined, { timeout: 5000 });
      const content = page.locator('[data-testid="advice-content"]');
      assert.strictEqual(await content.locator('img').count(), 0,
        '建议内容不得 innerHTML 注入 img 元素');
      assert.strictEqual(await content.locator('script').count(), 0,
        '建议内容不得产生 script 元素');
      assert.strictEqual(await page.evaluate(() => window.__xss), undefined,
        '注入的字面 HTML 不得执行');
      assert.ok(!(await btn.isDisabled()), '完成后按钮应恢复可用');
    },
  });

  // C3 —— A→B→A 竞态：最早发起的 A 最后返回，同学生 ID 的旧请求按序号丢弃
  tests.push({
    name: 'C3 A→B→A 竞态：最早 A 最后返回，同学生旧请求绝不覆盖新建议',
    run: async ({ page }) => {
      await mockStatus(page, true);
      let releaseA1;
      const gateA1 = new Promise((r) => { releaseA1 = r; });
      let a1EnteredResolve;
      const a1Entered = new Promise((r) => { a1EnteredResolve = r; });
      let a1SettledResolve;
      const a1Settled = new Promise((r) => { a1SettledResolve = r; });
      const seen = [];
      await page.route('**/api/students/*/advice', async (route) => {
        const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
        seen.push(sid);
        const isA1 = sid === 1 && seen.filter((x) => x === 1).length === 1;
        if (isA1) {
          a1EnteredResolve();   // 学生 1 的第一个请求已进入挂起 gate
          await gateA1;
        }
        let marker = '建议-学生' + sid;
        if (sid === 1) {
          marker = isA1 ? '建议-学生1-旧' : '建议-学生1-新';
        }
        try {
          await route.fulfill({ status: 200, contentType: 'application/json',
                                body: adviceBody(sid, marker) });
        } catch { /* 被前端 abort 属正确行为 */ }
        if (isA1) {
          a1SettledResolve();   // A1 已落定（响应或被 abort），明确 gate 信号
        }
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);
      const btn = page.locator('[data-testid="generate-advice"]');
      await btn.waitFor({ state: 'visible' });
      await btn.click(); // A1（学生 1 的第一个请求，被挂起）
      await Promise.race([a1Entered, timeout(5000, '学生1 首个建议请求未进入挂起 gate')]);

      // 切到 B：旧建议立即清空
      await page.locator('[data-testid="student-select"]').selectOption('2');
      const content = page.locator('[data-testid="advice-content"]');
      const txt = (await content.innerText().catch(() => '')).trim();
      const hidden = await content.isHidden().catch(() => true);
      assert.ok(txt === '' || hidden, '切学生后旧建议应立即清空');

      // B 生成（立即返回）
      await page.locator('[data-testid="generate-advice"]').click();
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes('建议-学生2');
      }, undefined, { timeout: 5000 });

      // 切回 A 并生成新建议（A2，立即返回）
      await page.locator('[data-testid="student-select"]').selectOption('1');
      await page.locator('[data-testid="generate-advice"]').click();
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes('建议-学生1-新');
      }, undefined, { timeout: 5000 });

      // 释放最早发起的 A1（最后返回）；用明确 gate 信号而非固定 sleep 作完成判据
      releaseA1();
      await Promise.race([a1Settled, timeout(5000, 'A1 旧请求未落定')]);
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes('建议-学生1-新');
      }, undefined, { timeout: 5000 });
      const final = await content.innerText();
      assert.ok(final.includes('建议-学生1-新'), '新建议不得被旧请求覆盖');
      assert.ok(!final.includes('建议-学生1-旧'), '同学生 ID 的旧响应绝不得显示');
      assert.ok(!final.includes('建议-学生2'), '其它学生的建议不得显示在当前学生');
    },
  });

  // C4 —— 失败仅一次请求；手动重试恰好第二次；独立于诊断；预期 502 豁免
  tests.push({
    name: 'C4 失败后恰好一次请求，手动重试恰好第二次，不影响诊断区',
    run: async ({ page, expectFail }) => {
      await mockStatus(page, true);
      let fail = true;
      let attempts = 0;
      await page.route('**/api/students/*/advice', (route) => {
        attempts += 1;
        if (fail) {
          route.fulfill({
            status: 502, contentType: 'application/json',
            body: JSON.stringify({ error: { code: 'LLM_UPSTREAM_ERROR',
                                            message: '上游服务错误，请重试' } }),
          });
        } else {
          const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
          route.fulfill({ status: 200, contentType: 'application/json',
                          body: adviceBody(sid, '重试成功') });
        }
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);
      await page.locator('[data-testid="generate-advice"]').waitFor({ state: 'visible' });
      // 显式豁免：本测试注入 URL 的预期 5xx 资源 console.error
      expectFail(baseURL + '/api/students/1/advice');
      await page.locator('[data-testid="generate-advice"]').click();

      const err = page.locator('[data-testid="advice-error"]');
      await err.waitFor({ state: 'visible', timeout: 5000 });
      assert.strictEqual(await err.getAttribute('role'), 'alert');
      assert.ok(/[一-鿿]/.test(await err.innerText()), '错误信息须中文');
      const retry = page.locator('[data-testid="advice-retry"]');
      await retry.waitFor();
      assert.ok((await retry.innerText()).includes('重试'));
      // 预期 502 的注入记录保留至页面关闭，不提前清除（容忍迟到日志；豁免范围按 URL+5xx 严格限定）
      assert.strictEqual(attempts, 1, '失败后必须恰好只有一次付费请求');
      assert.strictEqual(await page.locator('[data-testid="radar-chart"]').count(), 1,
        '建议区错误不得影响诊断区');

      fail = false;
      await retry.click(); // 手动重试，恰好第二次
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes('重试成功');
      }, undefined, { timeout: 5000 });
      assert.strictEqual(attempts, 2, '手动重试应恰好是第二次请求');
      await err.waitFor({ state: 'hidden', timeout: 5000 });
    },
  });

  // C5 —— 状态查询失败 / 未配置 / 恢复：独立中文错误与手动重试（只 GET），
  //       绝不误报「未配置」、绝不自动发付费 POST；切学生不污染
  tests.push({
    name: 'C5 状态失败→独立错误+仅GET重试→恢复后仅手动一次生成；未配置不误报',
    run: async ({ page, expectFail }) => {
      let statusMode = 'fail'; // 'fail' | 'ok' | 'unconfigured'
      let postCount = 0;
      let statusGets = 0;
      let onStatusGetResolve = null;
      const statusGate = () => new Promise((r) => { onStatusGetResolve = r; });
      await page.route('**/api/llm/status', (route) => {
        statusGets += 1;
        if (onStatusGetResolve) {
          const f = onStatusGetResolve;
          onStatusGetResolve = null;
          f();
        }
        if (statusMode === 'fail') {
          route.fulfill({
            status: 500, contentType: 'application/json',
            body: JSON.stringify({ error: { code: 'INTERNAL',
                                            message: '服务器内部错误' } }),
          });
        } else {
          route.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify(statusMode === 'ok'
              ? { configured: true, provider: 'deepseek', model: 'deepseek-v4-pro',
                  reasoning_effort: 'max' }
              : { configured: false, provider: null, model: null,
                  reasoning_effort: null }),
          });
        }
      });
      await page.route('**/api/students/*/advice', (route) => {
        postCount += 1;
        const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
        route.fulfill({ status: 200, contentType: 'application/json',
                        body: adviceBody(sid, '配置后生成') });
      });

      expectFail(baseURL + '/api/llm/status'); // 注入的状态 500 为预期资源错误
      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);

      const err = page.locator('[data-testid="advice-error"]');
      const retry = page.locator('[data-testid="advice-retry"]');
      const missing = page.locator('[data-testid="advice-config-missing"]');
      const btn = page.locator('[data-testid="generate-advice"]');

      // 状态查询失败：独立中文错误；绝不显示「未配置」；绝不发付费 POST
      await err.waitFor({ state: 'visible', timeout: 10000 });
      assert.strictEqual(await err.getAttribute('role'), 'alert');
      assert.ok((await err.innerText()).includes('无法获取模型配置状态'),
        '状态失败须明确提示状态错误');
      assert.ok(!(await missing.isVisible().catch(() => false)),
        '状态失败不得显示「未配置」');
      assert.ok(!(await btn.isVisible().catch(() => false)),
        '状态失败不得显示生成按钮');
      assert.strictEqual(postCount, 0, '状态失败不得发付费 POST');

      // 手动重试仍失败：只再 GET 一次状态，绝不 POST
      let gate = statusGate();
      await retry.click();
      await Promise.race([gate, timeout(5000, '状态重试 GET 未被捕获')]);
      assert.ok((await err.innerText()).includes('无法获取模型配置状态'));
      assert.strictEqual(postCount, 0, '状态重试只 GET，绝不 POST');

      // 状态恢复（configured）：重试成功后按钮启用；仍必须点击生成才付费
      // （预期 500 的注入记录保留至页面关闭，不提前清除，容忍迟到日志）
      statusMode = 'ok';
      gate = statusGate();
      await retry.click();
      await Promise.race([gate, timeout(5000, '状态恢复 GET 未被捕获')]);
      await btn.waitFor({ state: 'visible', timeout: 5000 });
      await err.waitFor({ state: 'hidden', timeout: 5000 });
      assert.ok(!(await missing.isVisible().catch(() => false)));
      assert.strictEqual(postCount, 0, '状态恢复后仍不得自动发付费 POST');
      await btn.click();
      await page.waitForFunction(() => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes('配置后生成');
      }, undefined, { timeout: 5000 });
      assert.strictEqual(postCount, 1, '必须点击生成才发付费 POST');

      // 未配置：刷新后明确「未配置」（可见隐藏容器），无按钮、无 POST，且不是错误态
      statusMode = 'unconfigured';
      await page.reload({ waitUntil: 'domcontentloaded' });
      await waitReady(page);
      await missing.waitFor({ state: 'visible', timeout: 10000 });
      assert.ok((await missing.innerText()).includes('未配置'), '须明确提示未配置');
      assert.ok(!(await btn.isVisible().catch(() => false)), '未配置时按钮不得可见');
      assert.ok(!(await err.isVisible().catch(() => false)), '未配置不是错误态');
      assert.strictEqual(postCount, 1);

      // 切学生：旧状态失败不得污染新学生（新学生状态成功 → 按钮启用、错误清除）
      statusMode = 'fail';
      expectFail(baseURL + '/api/llm/status');
      await page.locator('[data-testid="student-select"]').selectOption('2');
      await err.waitFor({ state: 'visible', timeout: 5000 }); // 学生 2 的状态失败
      statusMode = 'ok';
      await page.locator('[data-testid="student-select"]').selectOption('3');
      await btn.waitFor({ state: 'visible', timeout: 5000 }); // 学生 3 状态成功
      await err.waitFor({ state: 'hidden', timeout: 5000 });
      assert.ok(!(await missing.isVisible().catch(() => false)));
      assert.strictEqual(postCount, 1, '切换/状态重试绝不发付费 POST');
    },
  });

  // C6 —— 真实 Tab 聚焦 + Space 键盘激活；390px 长英文单词换行不溢出
  tests.push({
    name: 'C6 Tab/Space 键盘激活按钮；390px 长英文单词换行无横向溢出',
    viewport: 'mobile',
    run: async ({ page }) => {
      await mockStatus(page, true);
      const longWord = 'Supercalifragilisticexpialidocious'.repeat(3); // 合法连续英文长词
      let capturedResolve;
      const captured = new Promise((r) => { capturedResolve = r; });
      await page.route('**/api/students/*/advice', (route) => {
        capturedResolve();
        const sid = parseInt((route.request().url().match(SID_RE) || [])[1], 10);
        route.fulfill({ status: 200, contentType: 'application/json',
                        body: adviceBody(sid, longWord) });
      });

      await page.goto(baseURL + '/', { waitUntil: 'domcontentloaded' });
      await waitReady(page);
      const btn = page.locator('[data-testid="generate-advice"]');
      await btn.waitFor({ state: 'visible' });

      // 真实键盘可达：Tab 遍历直到焦点落在按钮（不用 focus+鼠标 click 冒充键盘验收）
      let reached = false;
      for (let i = 0; i < 12; i++) {
        await page.keyboard.press('Tab');
        const id = await page.evaluate(() =>
          document.activeElement && document.activeElement.getAttribute('data-testid'));
        if (id === 'generate-advice') { reached = true; break; }
      }
      assert.ok(reached, 'Tab 无法到达建议按钮');
      const style = await btn.evaluate((el) => {
        const cs = getComputedStyle(el);
        return { outline: cs.outlineStyle, shadow: cs.boxShadow };
      });
      assert.ok(style.outline !== 'none' || style.shadow !== 'none',
        '按钮键盘聚焦无可见焦点指示');

      await page.keyboard.press('Space'); // 真实键盘激活
      await Promise.race([captured, timeout(5000, '键盘激活未触发 POST')]);
      await page.waitForFunction((word) => {
        const el = document.querySelector('[data-testid="advice-content"]');
        return el && el.textContent.includes(word);
      }, longWord, { timeout: 5000 });

      const overflow = await page.evaluate(() => ({
        inner: window.innerWidth,
        doc: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
      }));
      assert.ok(overflow.inner <= 390);
      assert.ok(overflow.doc <= 390,
        `长英文单词未换行导致横向溢出：scrollWidth=${overflow.doc}`);
      assert.ok(overflow.body <= 390, `body 横向溢出：${overflow.body}`);
    },
  });

  return tests;
}

// ---------------------------------------------------------------------------
// 运行器（node:assert + playwright；兜底安全网 + 严格 JS 错误检查）
// ---------------------------------------------------------------------------

async function newPage(context) {
  const page = await context.newPage();
  const jsErrors = [];
  const expectFailUrls = new Set();
  page.on('pageerror', (e) => jsErrors.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const text = m.text();
    // 仅豁免本 case 明确注入 URL 的预期资源错误：按 console 消息 location().url 精确匹配
    // 且状态码为确切 5xx；location 缺失不得泛化豁免；注入记录保留至页面关闭，
    // 容忍故意失败（500/502）的 console 日志晚于 UI 状态出现。
    if (expectFailUrls.size > 0 &&
        /Failed to load resource|the server responded with a status of 5\d\d/i.test(text)) {
      const loc = m.location ? m.location() : null;
      const url = loc && loc.url ? loc.url : '';
      if (url && expectFailUrls.has(url)) {
        return;
      }
    }
    jsErrors.push(`console.error: ${text}`);
  });
  return {
    page,
    jsErrors,
    expectFail: (u) => expectFailUrls.add(u),
    close: () => page.close(),
  };
}

async function runCase(t, ctx) {
  try {
    await t.run(ctx);
    assert.deepStrictEqual(ctx.unexpected, [],
      '存在未被 mock 接管的付费 POST（已 abort 防真实 API）：' + ctx.unexpected.join(', '));
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
  const screenshotDir = process.env.E2E_SCREENSHOT_DIR || 'docs/validation';
  const baseURL = (process.env.E2E_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
  const all = [];
  let failed = 0;

  console.log(`被测服务：${baseURL}`);
  let browser;
  try {
    const { chromium } = require('playwright');
    browser = await chromium.launch({ headless: true });
    const bt = browserTests(baseURL);
    const desktop = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    for (const t of bt.filter((x) => (x.viewport || 'desktop') === 'desktop')) {
      const ctx = await newPage(desktop);
      ctx.unexpected = installSafetyNet(ctx.page);
      const r = await runCase(t, ctx);
      all.push(r);
      if (!r.ok) {
        failed += 1;
        const shot = path.join(screenshotDir, 'advice-red-failure.png');
        try {
          fs.mkdirSync(screenshotDir, { recursive: true });
          await ctx.page.screenshot({ path: shot, fullPage: true }).catch(() => {});
        } catch { /* 截图失败不掩盖主错误 */ }
      }
      await ctx.close().catch(() => {});
    }
    await desktop.close().catch(() => {});
    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
    for (const t of bt.filter((x) => x.viewport === 'mobile')) {
      const ctx = await newPage(mobile);
      ctx.unexpected = installSafetyNet(ctx.page);
      const r = await runCase(t, ctx);
      all.push(r);
      if (!r.ok) failed += 1;
      await ctx.close().catch(() => {});
    }
    await mobile.close().catch(() => {});
    await browser.close().catch(() => {});
  } catch (e) {
    failed += 1;
    all.push({ name: '浏览器 E2E（整体）', ok: false,
               error: new Error(`浏览器不可用/未启动：${e.message.split('\n')[0]}`) });
    console.log(`  ✘ ${all[all.length - 1].error.message}`);
  }

  console.log('\n──────────────────────────────');
  const pass = all.filter((r) => r.ok).length;
  const fail = all.filter((r) => !r.ok).length;
  console.log(`结果：${pass} 通过 / ${fail} 失败（共 ${all.length} 项）`);
  for (const r of all.filter((x) => !x.ok)) {
    console.log(`  - ${r.name}\n    ${r.error && r.error.message ? r.error.message.split('\n')[0] : ''}`);
  }
  console.log(`EXIT_CODE=${fail > 0 ? 1 : 0}`);
  process.exitCode = fail > 0 ? 1 : 0;
}

main().catch((e) => {
  console.error('运行器异常：', e);
  process.exitCode = 1;
});
