"""LLM 学习建议（加分项）—— 纯标准库实现，契约见 docs/LLM_SUGGESTIONS.md。

- 密钥仅由服务端注入（环境 DEEPSEEK_API_KEY 或 --prompt-key），本模块不读、不存任何密钥。
- 默认网络层：单线程、`read1` 单次有界读取（禁止聚合 read）、仅在响应读取环节检查整体截止、
  socket 空闲超时立即关闭并返回 TIMEOUT、禁重定向、不自动重试、输入/输出字节受限、
  异常与上游 body/密钥一律不回显。
- 结构化校验：JSON mode 不替代应用校验；未知字段剥离；布尔 kp_id 拒绝；仅 finish_reason=stop。
"""

import http.client
import json
import socket
import time
import urllib.error
import urllib.request

MODEL = "deepseek-v4-pro"
PROVIDER_URL = "https://api.deepseek.com/chat/completions"
REASONING_EFFORT = "max"
MAX_REQUEST_BYTES = 4096        # 客户端 POST 请求体上限（严格 {}，4 KiB 足够）
MAX_PROMPT_BYTES = 16384        # 供应商完整请求 JSON 上限（中文诊断 + 约束，16 KiB）
MAX_RESPONSE_BYTES = 1_048_576  # 供应商响应上限（1 MiB）
MAX_CONCURRENT_ADVICE = 1
SOCKET_TIMEOUT = 60.0           # socket 空闲超时（连接/代理/TLS 阶段约束）
OVERALL_DEADLINE = 120.0        # 响应读取截止检查（不声称整次请求墙钟上限）
MAX_SUMMARY_LEN = 300
MAX_REASON_LEN = 200
MAX_ACTION_LEN = 200
MAX_CHECK_LEN = 200

# 上游 HTTP 状态 → 错误码（其余状态一律 LLM_UPSTREAM_ERROR）
_HTTP_ERROR_CODES = {
    401: "LLM_UNAUTHORIZED",
    402: "LLM_PAYMENT_REQUIRED",
    429: "LLM_RATE_LIMITED",
}

_ERROR_MESSAGES = {
    "LLM_UNAUTHORIZED": "模型服务鉴权失败，请检查服务端密钥配置",
    "LLM_PAYMENT_REQUIRED": "模型账户余额或付费状态不可用，请稍后手动重试",
    "LLM_RATE_LIMITED": "模型服务繁忙，请稍后手动重试",
    "LLM_UPSTREAM_ERROR": "模型服务返回异常状态",
    "TIMEOUT": "模型服务响应超时，请稍后手动重试",
    "NETWORK": "网络异常，无法连接模型服务",
    "BAD_RESPONSE": "模型返回内容异常，请稍后手动重试",
}


class AdviceError(Exception):
    """code ∈ {BAD_ADVICE, BAD_REQUEST, REQUEST_TOO_LARGE, INTERNAL,
               LLM_UNAUTHORIZED, LLM_PAYMENT_REQUIRED, LLM_RATE_LIMITED,
               LLM_UPSTREAM_ERROR, TIMEOUT, NETWORK, BAD_RESPONSE}"""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class DeadlineError(Exception):
    """整体响应读取截止触发（default_transport 内部使用，call_provider 映射为 TIMEOUT）。"""


# ---------------------------------------------------------------------------
# 客户端请求体校验
# ---------------------------------------------------------------------------

def check_request_json(body):
    """严格 {}（允许首尾空白）；> MAX_REQUEST_BYTES → REQUEST_TOO_LARGE；其余畸形 → BAD_REQUEST。"""
    if len(body) > MAX_REQUEST_BYTES:
        raise AdviceError("REQUEST_TOO_LARGE", "请求体过大")
    try:
        obj = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdviceError("BAD_REQUEST", "请求体必须是 JSON")
    if not isinstance(obj, dict) or len(obj) != 0:
        raise AdviceError("BAD_REQUEST", "请求体必须严格为 {}")


# ---------------------------------------------------------------------------
# 提示词与建议结构
# ---------------------------------------------------------------------------

def build_prompt(mastery, correct_rate, kps, edges):
    """中文提示词：掌握概率是估计且与答对率区分；薄弱知识与前置关系；练习动作与检查方法；
    不编造学生经历；合成小样本局限。掌握概率/答对率 3 位小数；边以 KP<parent>→KP<child> 列出。"""
    lines = [
        "你是小学数学教师。请根据下面的认知诊断数据，为这名学生生成个性化学习建议。",
        "",
        "重要口径：",
        "- 「掌握概率」是 DINA 模型的统计估计值（0~1），不是确定判定，也与「答对率」不同；"
        "答对率只统计做对的比例，仅作对照。",
        "- 请优先关注掌握概率较低、并且是后续知识前置的薄弱知识点。",
        "- 建议要给出具体可执行的练习动作和检查方法，不得编造学生的测验成绩、课堂表现等经历。",
        "- 本数据为合成小样本（12 人 × 24 题），估计方差较大，结论仅供演示，不要过度断言。",
        "",
        "知识点（%s）：" % "、".join(name for (_kid, name) in kps),
        "学生当前数据（掌握概率与答对率）：",
    ]
    for (kp_id, name, prob), (_kid, _cname, rate) in zip(mastery, correct_rate):
        lines.append("- KP%d %s：掌握概率 %.3f，答对率 %.3f" % (kp_id, name, prob, rate))
    lines.append("")
    lines.append("知识点前置关系（KP前置→KP后续）：")
    for parent, child in edges:
        lines.append("- KP%d→KP%d" % (parent, child))
    lines.append("")
    lines.append("请只输出一个 JSON 对象（不要任何其它文字），结构如下：")
    lines.append(
        '{"summary": "总体建议（≤300字）", "priorities": [{"kp_id": 整数（1~5，互异，1~3 项）, '
        '"reason": "原因（≤200字）", "actions": ["具体练习动作（1~3 条，每条≤200字）"], '
        '"check": "检查方法（≤200字）"}]}')
    return "\n".join(lines)


def _bad(message):
    raise AdviceError("BAD_ADVICE", message)


def _check_text(value, max_len, label):
    if not isinstance(value, str):
        _bad("%s 必须为字符串" % label)
    if not value.strip():
        _bad("%s 不得为空" % label)
    if len(value) > max_len:
        _bad("%s 超过长度上限" % label)
    return value


def parse_advice(content, known_kp_ids):
    """校验并规范化建议 JSON；未知字段剥离（仅返回固定键）；违反结构契约 → BAD_ADVICE。"""
    if not isinstance(content, str) or not content.strip():
        _bad("模型返回内容为空")
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        _bad("模型返回不是合法 JSON")
    if not isinstance(obj, dict):
        _bad("模型返回结构不是 JSON 对象")
    summary = _check_text(obj.get("summary"), MAX_SUMMARY_LEN, "summary")
    raw_priorities = obj.get("priorities")
    if not isinstance(raw_priorities, list):
        _bad("priorities 必须为数组")
    if not 1 <= len(raw_priorities) <= 3:
        _bad("priorities 必须为 1~3 项")
    known = list(known_kp_ids)
    priorities = []
    seen = set()
    for item in raw_priorities:
        if not isinstance(item, dict):
            _bad("priorities 每项必须为对象")
        kp_id = item.get("kp_id")
        if isinstance(kp_id, bool) or not isinstance(kp_id, int) or kp_id not in known:
            _bad("kp_id 必须是存在的知识点 ID")
        if kp_id in seen:
            _bad("kp_id 不得重复")
        seen.add(kp_id)
        reason = _check_text(item.get("reason"), MAX_REASON_LEN, "reason")
        actions = item.get("actions")
        if not isinstance(actions, list) or not 1 <= len(actions) <= 3:
            _bad("actions 必须为 1~3 条")
        norm_actions = [_check_text(a, MAX_ACTION_LEN, "actions 条目") for a in actions]
        check = _check_text(item.get("check"), MAX_CHECK_LEN, "check")
        priorities.append({"kp_id": kp_id, "reason": reason,
                           "actions": norm_actions, "check": check})
    return {"summary": summary, "priorities": priorities}


# ---------------------------------------------------------------------------
# 供应商请求
# ---------------------------------------------------------------------------

def build_llm_payload(prompt):
    """锁定字段：model/thinking/reasoning_effort/response_format/stream/max_tokens，无 temperature。"""
    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "enabled"},
        "reasoning_effort": REASONING_EFFORT,
        "response_format": {"type": "json_object"},
        "stream": False,
        "max_tokens": 8192,
    }


def build_request(api_key, prompt):
    """(固定 PROVIDER_URL, 含 Bearer 的头, JSON body)；body 超过 MAX_PROMPT_BYTES → INTERNAL。"""
    body = json.dumps(build_llm_payload(prompt), ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_PROMPT_BYTES:
        raise AdviceError("INTERNAL", "提示词超过内部上限，无法发送")
    headers = {"Authorization": "Bearer " + api_key,
               "Content-Type": "application/json"}
    return PROVIDER_URL, headers, body


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁用任何重定向：不返回新请求 → 3xx 由 HTTPErrorProcessor 抛为 HTTPError，
    因此绝不发起第二次请求、绝不把 Authorization 转发到异源。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_opener():
    """生产 opener：以 NoRedirect 子类禁重定向（行为由测试保证，不以 handler 类型内省作契约）。"""
    return urllib.request.build_opener(_NoRedirect())


# ---------------------------------------------------------------------------
# 默认网络层 / 供应商调用
# ---------------------------------------------------------------------------

def _status_code(resp):
    return resp.status if hasattr(resp, "status") else resp.code


def default_transport(url, data, headers, socket_timeout, deadline,
                      *, opener=None, clock=time.monotonic, chunk=65536):
    """默认网络层（单线程，不创建线程；只做单次有界 read1，禁止聚合 read）。

    - 每次 read1 前检查 clock() >= deadline → 关闭响应并抛 DeadlineError（读取截止检查）。
    - read1 抛 socket.timeout → 立即关闭响应并抛 AdviceError("TIMEOUT")（不继续轮询）。
    - read1 抛 HTTPException/IncompleteRead/ValueError → 关闭并抛 BAD_RESPONSE（脱敏）。
    - opener.open 抛 HTTPError（含 302/3xx）→ 按状态映射并关闭其 fp，不回显响应体/Location。
    - 任何路径 finally 关闭响应资源。
    """
    if opener is None:
        opener = build_opener()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        try:
            resp = opener.open(req, timeout=socket_timeout)
        except urllib.error.HTTPError as e:
            try:
                code = _HTTP_ERROR_CODES.get(e.code, "LLM_UPSTREAM_ERROR")
                raise AdviceError(code, _ERROR_MESSAGES[code])
            finally:
                try:
                    e.close()
                except Exception:
                    pass
        except socket.timeout:
            raise AdviceError("TIMEOUT", _ERROR_MESSAGES["TIMEOUT"])
        except urllib.error.URLError:
            raise AdviceError("NETWORK", _ERROR_MESSAGES["NETWORK"])
        except OSError:
            raise AdviceError("NETWORK", _ERROR_MESSAGES["NETWORK"])
        except http.client.HTTPException:
            # open 阶段真实 HTTPException（BadStatusLine/LineTooLong 等，非 OSError/URLError
            # 子类）→ 与读取阶段同样映射 BAD_RESPONSE，不得落成 500
            raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])

        try:
            chunks = []
            total = 0
            while True:
                if clock() >= deadline:
                    raise DeadlineError("响应读取截止")
                try:
                    part = resp.read1(chunk)
                except socket.timeout:
                    raise AdviceError("TIMEOUT", _ERROR_MESSAGES["TIMEOUT"])
                except http.client.HTTPException:
                    raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
                except (ValueError, OSError):
                    raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
                if not part:
                    break
                total += len(part)
                if total > MAX_RESPONSE_BYTES:
                    raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
                chunks.append(part)
            # 提前 EOF 校验：read1 在提前 EOF 时不保证抛 IncompleteRead，
            # 声明了 Content-Length 却仍有剩余未读 → 响应不完整，拒绝（无 CL 的响应 length=None 正常支持）
            remaining = getattr(resp, "length", None)
            if remaining is not None and remaining > 0:
                raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
            body = b"".join(chunks)
            return _status_code(resp), dict(resp.headers.items()), body
        finally:
            try:
                resp.close()
            except Exception:
                pass
    finally:
        pass


def call_provider(transport, api_key, prompt, *, overall_deadline=OVERALL_DEADLINE):
    """构造请求并调用注入的 transport；映射异常为 AdviceError；不自动重试；
    只取 choices[0].message.content（忽略 reasoning_content）；仅 finish_reason=stop 成功。"""
    url, headers, body = build_request(api_key, prompt)
    deadline = time.monotonic() + overall_deadline
    try:
        status, _resp_headers, raw = transport(
            url, body, headers, SOCKET_TIMEOUT, deadline)
    except DeadlineError:
        raise AdviceError("TIMEOUT", _ERROR_MESSAGES["TIMEOUT"])
    except socket.timeout:
        raise AdviceError("TIMEOUT", _ERROR_MESSAGES["TIMEOUT"])
    except urllib.error.URLError:
        raise AdviceError("NETWORK", _ERROR_MESSAGES["NETWORK"])
    except OSError:
        raise AdviceError("NETWORK", _ERROR_MESSAGES["NETWORK"])
    except AdviceError:
        raise
    if len(raw) > MAX_RESPONSE_BYTES:
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    if status != 200:
        code = _HTTP_ERROR_CODES.get(status, "LLM_UPSTREAM_ERROR")
        raise AdviceError(code, _ERROR_MESSAGES[code])
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    if not isinstance(obj, dict):
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    choices = obj.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    first = choices[0]
    if not isinstance(first, dict):
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    message = first.get("message")
    if not isinstance(message, dict):
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    finish = first.get("finish_reason")
    if finish != "stop":
        raise AdviceError("BAD_RESPONSE", _ERROR_MESSAGES["BAD_RESPONSE"])
    request_id = obj.get("id") if isinstance(obj.get("id"), str) else None
    usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else None
    return content, finish, request_id, usage


def status_payload(api_key):
    """非敏感状态；不含密钥。"""
    if not api_key:
        return {"configured": False, "provider": None,
                "model": None, "reasoning_effort": None}
    return {"configured": True, "provider": "deepseek",
            "model": MODEL, "reasoning_effort": REASONING_EFFORT}
