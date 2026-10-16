/* 学生认知诊断 —— 前端逻辑（零依赖，拉取只读 GET 接口渲染 SVG 与表格）。
 *
 * 数据全部来自后端 /api/*；本文件不内置任何掌握概率常量。
 * 快速切换用 AbortController 取消旧请求，防止旧结果覆盖新选择；
 * 请求失败只显示中文错误与重试，不把旧学生数据当作当前显示。
 */
(function () {
  'use strict';

  var state = {
    students: [],        // [{id, name}]
    graph: null,         // {nodes:[{id,code,name}], edges:[{parent,child}]}
    diagnosis: null,     // {matrix:[{student_id,kp_id,prob}]}
    currentId: null,
    abortController: null,
  };

  function $(sel) {
    return document.querySelector(sel);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function formatPct(p) {
    return (p * 100).toFixed(1) + '%';
  }

  // 深靛蓝渐变（仅辅助视觉；节点另有名称 + 百分比文本，颜色非唯一信息通道）。
  function colorFor(prob) {
    var t = Math.max(0, Math.min(1, prob));
    var r = Math.round(0x63 + (0x43 - 0x63) * t);
    var g = Math.round(0x66 + (0x38 - 0x66) * t);
    var b = Math.round(0xf1 + (0xca - 0xf1) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  function showLoading() {
    $('[data-testid="loading"]').hidden = false;
  }

  function hideLoading() {
    $('[data-testid="loading"]').hidden = true;
  }

  function showError(message, retryFn) {
    var errorEl = $('[data-testid="error"]');
    var retryEl = $('[data-testid="retry"]');
    errorEl.textContent = message;
    errorEl.hidden = false;
    retryEl.hidden = false;
    retryEl.onclick = retryFn;
  }

  function hideError() {
    $('[data-testid="error"]').hidden = true;
    $('[data-testid="retry"]').hidden = true;
  }

  // 清空当前学生的三块诊断视图（雷达 / 概率表 / 图谱），避免旧数据归属到新学生。
  function clearCurrentDiagnosis() {
    $('#radar').innerHTML = '';
    $('[data-testid="mastery-table"] tbody').innerHTML = '';
    $('#graph').innerHTML = '';
  }

  async function fetchJSON(path, options) {
    var resp = await fetch(path, options);
    if (!resp.ok) {
      throw new Error('HTTP ' + resp.status + ' ' + path);
    }
    return resp.json();
  }

  // ---- 渲染 ----

  function renderSelect() {
    var select = $('[data-testid="student-select"]');
    select.innerHTML = state.students.map(function (s) {
      return '<option value="' + s.id + '">' + escapeHtml(s.name) + '</option>';
    }).join('');
    select.value = '1'; // 默认第一个学生
    select.addEventListener('change', function () {
      loadStudentDetail(parseInt(select.value, 10));
    });
    // macOS Chromium 的原生 select 不响应 Home/End；显式处理首/末项并复用同一 change 加载逻辑，
    // 保持方向键/原生可访问性不变。
    select.addEventListener('keydown', function (e) {
      if (e.key !== 'Home' && e.key !== 'End') {
        return;
      }
      e.preventDefault();
      var opts = select.options;
      if (opts.length === 0) {
        return;
      }
      select.selectedIndex = e.key === 'Home' ? 0 : opts.length - 1;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }

  function renderRadar(mastery, studentName) {
    var container = $('#radar');
    var cx = 170, cy = 170, R = 110;
    var probs = mastery.map(function (m) { return m.prob; });
    var names = mastery.map(function (m) { return m.name; });
    var n = probs.length;

    // 雷达轴标签用短名，避免中文长名溢出画布（表格/图谱仍用完整名）。
    var shortNames = { '应用题建模/列式': '应用题' };
    function axisLabel(name) {
      return shortNames[name] || name;
    }

    function vertex(i, r) {
      var ang = -Math.PI / 2 + i * (2 * Math.PI / n);
      return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)];
    }
    function polyPoints(scale) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var p = vertex(i, R * scale);
        pts.push(p[0].toFixed(2) + ',' + p[1].toFixed(2));
      }
      return pts.join(' ');
    }

    // 网格 + 轴
    var grid = '';
    for (var lv = 1; lv <= 5; lv++) {
      grid += '<polygon points="' + polyPoints(lv / 5) +
        '" fill="none" stroke="#e5e7eb" stroke-width="1"></polygon>';
    }
    var axes = '';
    for (var a = 0; a < n; a++) {
      var ap = vertex(a, R);
      axes += '<line x1="' + cx + '" y1="' + cy + '" x2="' + ap[0].toFixed(2) +
        '" y2="' + ap[1].toFixed(2) + '" stroke="#e5e7eb" stroke-width="1"></line>';
    }

    // 数值多边形（几何即概率：顶点距中心 = R × prob）
    var valuePts = [];
    for (var v = 0; v < n; v++) {
      var vp = vertex(v, R * probs[v]);
      valuePts.push(vp[0].toFixed(2) + ',' + vp[1].toFixed(2));
    }

    // 标签 + 数值（每轴共用同一外侧锚点 lp=vertex(k,R+32)：名称 y=lp.y-5、百分比 y=lp.y+11，
    // 相同 x、text-anchor middle，固定垂直两行，不随概率顶点位置）
    var labels = '';
    for (var k = 0; k < n; k++) {
      var lp = vertex(k, R + 32);
      labels += '<text x="' + lp[0].toFixed(2) + '" y="' + (lp[1] - 5).toFixed(2) +
        '" text-anchor="middle" font-size="12" fill="#374151">' +
        escapeHtml(axisLabel(names[k])) + '</text>';
      labels += '<text x="' + lp[0].toFixed(2) + '" y="' + (lp[1] + 11).toFixed(2) +
        '" text-anchor="middle" font-size="11" fill="#4f46e5">' +
        formatPct(probs[k]) + '</text>';
    }

    container.innerHTML =
      '<svg data-testid="radar-chart" role="img" aria-label="' +
      escapeHtml(studentName) + ' 的掌握概率雷达图" ' +
      'data-values="' + probs.join(',') + '" ' +
      'data-center="' + cx + ',' + cy + '" data-radius="' + R + '" ' +
      'viewBox="0 0 340 340" xmlns="http://www.w3.org/2000/svg">' +
      grid + axes +
      '<polygon data-testid="radar-polygon" points="' + valuePts.join(' ') +
      '" fill="#4f46e5" fill-opacity="0.35" stroke="#4f46e5" stroke-width="2"></polygon>' +
      labels +
      '</svg>';
  }

  function renderMasteryTable(mastery, correctRate) {
    var tbody = $('[data-testid="mastery-table"] tbody');
    var rateMap = {};
    correctRate.forEach(function (r) { rateMap[r.kp_id] = r.rate; });
    tbody.innerHTML = mastery.map(function (m) {
      return '<tr data-testid="mastery-row" data-kp-id="' + m.kp_id + '">' +
        '<th scope="row">' + escapeHtml(m.name) + '</th>' +
        '<td data-testid="mastery-value" data-value="' + m.prob + '">' +
        formatPct(m.prob) + '</td>' +
        '<td data-testid="correct-rate-value" data-value="' + rateMap[m.kp_id] + '">' +
        formatPct(rateMap[m.kp_id]) + '</td>' +
        '</tr>';
    }).join('');
  }

  function renderGraph(mastery) {
    var container = $('#graph');
    var probMap = {};
    mastery.forEach(function (m) { probMap[m.kp_id] = m.prob; });

    // 固定布局（5 节点 DAG：KP1 顶，KP2/KP4 中，KP3 左下，KP5 底；为下方名称留空间）
    var layout = {
      1: { x: 200, y: 36 },
      2: { x: 90, y: 150 },
      3: { x: 90, y: 270 },
      4: { x: 310, y: 150 },
      5: { x: 200, y: 340 },
    };
    var NODE_R = 30;

    var marker = '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" ' +
      'markerWidth="7" markerHeight="7" orient="auto-start-reverse">' +
      '<path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"></path></marker></defs>';

    var edges = state.graph.edges.map(function (e) {
      var a = layout[e.parent], b = layout[e.child];
      var dx = b.x - a.x, dy = b.y - a.y;
      var len = Math.hypot(dx, dy) || 1;
      var x2 = b.x - (dx / len) * NODE_R;
      var y2 = b.y - (dy / len) * NODE_R;
      return '<line data-testid="graph-edge" data-parent="' + e.parent +
        '" data-child="' + e.child + '" marker-end="url(#arrow)" ' +
        'x1="' + a.x + '" y1="' + a.y + '" x2="' + x2.toFixed(2) +
        '" y2="' + y2.toFixed(2) + '" stroke="#9ca3af" stroke-width="2"></line>';
    }).join('');

    var nodes = state.graph.nodes.map(function (n) {
      var p = layout[n.id];
      var prob = probMap[n.id];
      // 圆内只放百分比（白字）；完整名称用深色放在圆外下方，避免长名溢出圆在浅底不可读。
      return '<g data-testid="graph-node" data-kp-id="' + n.id +
        '" data-value="' + prob + '">' +
        '<circle cx="' + p.x + '" cy="' + p.y + '" r="' + NODE_R +
        '" fill="' + colorFor(prob) + '" stroke="#4f46e5" stroke-width="1.5"></circle>' +
        '<text data-testid="graph-node-value" x="' + p.x + '" y="' + (p.y + 5) +
        '" text-anchor="middle" font-size="13" font-weight="600" fill="#ffffff">' +
        formatPct(prob) + '</text>' +
        '<text data-testid="graph-node-name" x="' + p.x + '" y="' + (p.y + 44) +
        '" text-anchor="middle" font-size="12" fill="#1f2937">' +
        escapeHtml(n.name) + '</text>' +
        '</g>';
    }).join('');

    container.innerHTML =
      '<svg data-testid="knowledge-graph" role="img" ' +
      'aria-label="前置知识图谱（箭头表示前置指向后续）" ' +
      'viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">' +
      marker + edges + nodes + '</svg>';
  }

  function renderMatrix() {
    var table = $('[data-testid="all-students-table"]');
    var kps = state.graph.nodes; // KP1..KP5 顺序
    var probMap = {};
    state.diagnosis.matrix.forEach(function (r) {
      probMap[r.student_id + ':' + r.kp_id] = r.prob;
    });

    var head = '<thead><tr><th scope="col">学生</th>' +
      kps.map(function (k) {
        return '<th scope="col">' + escapeHtml(k.name) + '</th>';
      }).join('') + '</tr></thead>';

    var body = '<tbody>' + state.students.map(function (s) {
      var cells = kps.map(function (k) {
        var prob = probMap[s.id + ':' + k.id];
        return '<td data-testid="matrix-cell" data-student-id="' + s.id +
          '" data-kp-id="' + k.id + '" data-value="' + prob + '">' +
          formatPct(prob) + '</td>';
      }).join('');
      return '<tr data-testid="matrix-row" data-student-id="' + s.id + '">' +
        '<th scope="row">' + escapeHtml(s.name) + '</th>' + cells + '</tr>';
    }).join('') + '</tbody>';

    table.innerHTML = head + body;
  }

  function highlightMatrixRow(id) {
    document.querySelectorAll('[data-testid="matrix-row"]').forEach(function (row) {
      var isCurrent = row.getAttribute('data-student-id') === String(id);
      row.classList.toggle('current', isCurrent);
      if (isCurrent) {
        row.setAttribute('aria-current', 'true');
      } else {
        row.removeAttribute('aria-current');
      }
    });
  }

  function renderStudent(data) {
    renderRadar(data.mastery, data.student.name);
    renderMasteryTable(data.mastery, data.correct_rate);
    renderGraph(data.mastery);
    highlightMatrixRow(data.student.id);
  }

  // ---- 数据加载 ----

  async function loadStudentDetail(id) {
    var select = $('[data-testid="student-select"]');
    var currentEl = $('[data-testid="current-student"]');

    if (state.abortController) {
      state.abortController.abort();
    }
    var ac = new AbortController();
    state.abortController = ac;

    // 请求开始：立即清空旧诊断、清旧错误、显示中文加载态，避免旧数据归属到新学生。
    var name = (state.students.find(function (s) { return s.id === id; }) ||
      { name: '学生' + id }).name;
    clearCurrentDiagnosis();
    hideError();
    showLoading();
    currentEl.textContent = name + '（加载中）';

    try {
      var data = await fetchJSON('/api/students/' + id, { signal: ac.signal });
      if (ac.signal.aborted) {
        return; // 已被更新的请求取代，忽略本次结果（不结束新请求的加载态）
      }
      state.currentId = id;
      if (select.value !== String(id)) {
        select.value = String(id);
      }
      currentEl.textContent = data.student.name;
      renderStudent(data);
      hideError();
      hideLoading(); // 仅当前请求成功才结束加载
    } catch (e) {
      if (e.name === 'AbortError' || ac.signal.aborted) {
        return; // 旧请求被中止，不影响新请求的加载/错误状态
      }
      // 请求失败：诊断保持清空，明确标记失败，不把旧学生数据当作当前显示。
      currentEl.textContent = name + '（加载失败）';
      hideLoading();
      showError('学生数据加载失败，请重试', function () {
        loadStudentDetail(id);
      });
    }
  }

  async function loadInitial() {
    showLoading();
    hideError();
    try {
      var results = await Promise.all([
        fetchJSON('/api/students'),
        fetchJSON('/api/graph'),
        fetchJSON('/api/diagnosis'),
      ]);
      state.students = results[0].students;
      state.graph = results[1];
      state.diagnosis = results[2];
      renderSelect();
      renderMatrix();
      await loadStudentDetail(1); // 默认第一个学生
      hideLoading();
    } catch (e) {
      hideLoading();
      showError('加载失败，请重试', loadInitial);
    }
  }

  loadInitial();
})();
