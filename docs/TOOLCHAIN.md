# 工具链与模型路由说明（如实记录）

本文件说明本项目的**真实工具链与模型路由**，不读取任何 API Key、凭据、原始诊断包或完整转录；
依据项目内 `docs/evidence/` 的**脱敏**证据（仅配置确认、插件安装/真实 Skill 调用、UI 回归顺序元数据）。

## 1. 实际过程与分工

- **操作端**：Codex 代用户操作 **Claude Desktop Code**。
- **开发端**：代码、测试、文档由 **Claude Code 会话中配置的 DeepSeek 模型**生成（「Claude」指 Claude Code
  客户端/会话，不指 Anthropic 模型），并真实调用 Superpowers 工作流。
- **编排端**：Codex 负责**本地 git 编排**（`git init` / `add` / `commit`）与**外部 QA**
  （在沙箱外原样运行同一测试脚本、启动浏览器）。
- **限制处理**：Claude 沙箱内 `.git` 写入、本地端口绑定（`socket.bind` → EPERM）、浏览器进程
  注册受限，故**提交与 HTTP/浏览器验收由外部编排在沙箱外完成**，不是修改 Claude 沙箱设置，
  也不是把沙箱内的失败伪装成通过。

## 2. 模型路由

- 界面模型：**DeepSeek V4 Pro**，发送兼容别名 `claude-opus-4-8`，经 **DeepSeek Gateway** 路由
  （`https://api.deepseek.com/anthropic`）。
- 证据：`docs/evidence/03-routing-verification.json`（gateway endpoint / compatibility alias /
  display label 均命中，3p 模式，provider gateway ok）。
- 口径：系统里的「Claude Opus」名称是**兼容别名**，不能据此推断请求到达 Anthropic；模型自述
  也不是供应商身份验证。映射参考 DeepSeek 官方 Anthropic 兼容文档
  （`https://api-docs.deepseek.com/guides/anthropic_api/`）。
- 本会话**未读取任何 API Key**，也不声称读取过真实供应商内部身份。

## 3. Superpowers 插件与真实 Skill 调用

- 安装：`superpowers@claude-plugins-official`，版本 **7.0.0**，scope **user**，状态 **enabled**
  （证据 `docs/evidence/02-local-plugin-verification.txt`）。
- 真实 Skill 调用（证据 `docs/evidence/04-runtime-workflows.json`，仅工具元数据，无思考/签名/凭据）：
  - `superpowers:brainstorming` × 1（设计阶段，截图见 `docs/evidence/01-superpowers-brainstorming.png`）。
  - `superpowers:test-driven-development` × 3（算法 RED、后端 RED、前端 E2E 阶段）。

## 4. 测试/验证的落地

- Python 与浏览器测试脚本均由本会话生成；**外部编排在沙箱外**运行并回填真实输出：
  - Python：`docs/validation/python-external-final.txt`（79 项 OK）。
  - 前端：`docs/validation/frontend-external-final.txt`（15 组通过，6 HTTP + 9 浏览器）。
- 各阶段 RED/GREEN 的原始命令、退出码、输出保存在 `docs/validation/`，未通过项不打勾。

## 5. 过程真实性备注

- 核心算法/后端与前端初始契约有**真实测试先行**（git 历史 `docs → tests(RED) → feat(GREEN)`）。
- 个别 UI 回归（旧数据归属清空、节点长名外置）在 **QA 修复过程中追加** B8/B9 回归测试，
  并非全程都先 RED（证据 `docs/evidence/05-ui-regression-sequence.json`）。
- 详见 `docs/PROMPT_LOG.md` 的阶段记录与索引。
