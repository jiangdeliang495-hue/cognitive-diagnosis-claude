# 工具链与模型路由说明（如实记录）

本文件说明本项目的**真实工具链与模型路由**，不读取任何 API Key、凭据、原始诊断包或完整转录；
依据项目内 `docs/evidence/` 的**脱敏**证据（仅配置确认、插件安装/真实 Skill 调用、UI 回归顺序元数据）。

## 1. 实际过程与分工

- **操作端**：Codex 代用户操作 **Claude Desktop Code**。
- **前期开发端**：源码、测试及前期文档由 **Claude Code 会话中配置的 DeepSeek 模型**生成（「Claude」指客户端，不指 Anthropic 模型），实际调用 Superpowers。
- **本轮文档收尾**：用户授权 Codex 接手后，README、开发过程说明与各契约/提交草稿的当前状态由 Codex 编辑；PDF、验证编排与交付包也由 Codex 完成，不记为新的 DeepSeek 产出。
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
- 建议功能阶段另有一次真实 TDD 调用，返回未报错，见 `docs/evidence/07-llm-runtime-workflows.json`。合计 TDD 4 次，未通过修改旧证据扩大次数。
- 本次建议开发的界面 **DeepSeek V4 Pro Max** 见 `docs/evidence/06-llm-max-development.png`；不由此推断旧阶段全程最高思考。

## 4. 测试/验证的落地

- Python 与浏览器测试脚本由 Claude Code 会话生成；Codex 在沙箱外运行并保存实际输出。以下两项是核心阶段历史基线：
  - Python：`docs/validation/python-external-final.txt`（79 项 OK）。
  - 前端：`docs/validation/frontend-external-final.txt`（15 组通过，6 HTTP + 9 浏览器）。
- 各阶段 RED/GREEN 的原始命令、退出码、输出保存在 `docs/validation/`，未通过项不打勾。

## 5. 过程真实性备注

- 核心算法/后端与前端初始契约有**真实测试先行**（git 历史 `docs → tests(RED) → feat(GREEN)`）。
- 个别 UI 回归（旧数据归属清空、节点长名外置）在 **QA 修复过程中追加** B8/B9 回归测试，
  并非全程都先 RED（证据 `docs/evidence/05-ui-regression-sequence.json`）。
- 详见 `docs/PROMPT_LOG.md` 的阶段记录与索引。

## 6. 建议功能的最新验收与运行时

- 完整后端147/147：`docs/validation/advice-backend-external-final.txt`，包含原核心79项；使用模拟供应商和真实本机HTTP。
- 原前端15/15：`docs/validation/frontend-regression-with-advice.txt`；建议区模拟6/6：`docs/validation/advice-e2e-final-external.txt`。
- C5一次5/6来自故意500的console日志晚到，随后按注入URL限定过滤；失败记录原样保留，不当作业务失败或隐藏记录。
- **应用运行时调用与开发模型路由不同**：建议服务直接调用固定官方Chat Completions地址，`deepseek-v4-pro`、thinking开启、`reasoning_effort=max`、8192tokens。应用不能自动沿用Claude的Key，用户须通过服务端环境或getpass私下提供。
- 本机系统Python匿名TLS请求曾出现证书链失败；bundled Python保留默认验证时得到HTTP401，证明TLS可达，不证明Key有效或付费生成成功。不读取密钥链，不关闭证书验证。
- 真实付费DeepSeek成功调用尚未进行；新增桌面/390px截图为实际未配置状态。模型输出质量与真实计费行为仍需单独验收。
- 开发工具末尾再次返回402后，已完成的源码与测试保存为真实提交；最终文档由Codex接手，不伪造新的Claude提示词或DeepSeek记录。公开GitHub同步由用户授权，邮件仍未发送。
