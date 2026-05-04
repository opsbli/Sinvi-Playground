from __future__ import annotations

import json
import re

from .schemas import AgentDefinition


def is_tool_blocked_response(text: str) -> bool:
    normalized = str(text or "")
    return (
        "TOOL_EXECUTION_BLOCKED" in normalized
        or "TOOL_EXECUTION_NO_FINAL_ANSWER" in normalized
        or "response generation is blocked to avoid fabricated output" in normalized
    )


def format_tool_runtime_issue(text: str, agent: AgentDefinition) -> str:
    normalized = str(text or "").strip()
    if "TOOL_EXECUTION_NO_FINAL_ANSWER" in normalized or "did not produce a final answer" in normalized:
        return (
            f"{agent.name} 已完成工具调用，但执行器没有收敛出最终答案。"
            "这不是工具本身失败，而是工具后的总结阶段没有正常完成。"
            "本轮结果不应视为任务完成，应该继续调度、重试，或让其他节点接管。"
        )
    return normalized.replace("TOOL_EXECUTION_BLOCKED", "").strip()


def fallback_route(
    user_input: str,
    agents: list[AgentDefinition],
) -> tuple[str, str]:
    text = user_input.lower()
    ranked = []
    for agent in agents:
        score = 0
        haystack = f"{agent.name} {agent.description} {agent.system_prompt}".lower()
        for keyword in ("架构", "architecture", "design", "边界", "模块"):
            if keyword in text and keyword in haystack:
                score += 3
        for keyword in ("写", "总结", "文档", "改写", "说明"):
            if keyword in text and keyword in haystack:
                score += 3
        for keyword in ("学习", "路径", "怎么学", "建议", "步骤"):
            if keyword in text and keyword in haystack:
                score += 3
        ranked.append((score, agent))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = ranked[0][1]
    return selected.id, "当前处于无 API Key 的演示模式，使用关键词路由。"


def fallback_agent_response(
    agent: AgentDefinition,
    user_input: str,
    system_prompt: str,
) -> str:
    return (
        f"[演示模式] {agent.name} 正在处理用户请求。\n"
        f"角色说明：{agent.description}\n"
        f"有效系统提示词（含 skills 注入）：\n{system_prompt}\n"
        f"用户请求：{user_input}\n"
        "这里是一个占位回复；配置 OPENAI_API_KEY 后会切换成真实模型输出。"
    )


def parse_task_list(content: str, max_tasks: int) -> list[str]:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    parsed: object
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        bracket = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if not bracket:
            return []
        try:
            parsed = json.loads(bracket.group(0))
        except json.JSONDecodeError:
            return []

    items: list[str] = []
    if isinstance(parsed, list):
        items = [str(item).strip() for item in parsed if str(item).strip()]
    elif isinstance(parsed, dict) and isinstance(parsed.get("tasks"), list):
        items = [str(item).strip() for item in parsed["tasks"] if str(item).strip()]

    return items[:max_tasks]


def fallback_plan_tasks(user_input: str, max_tasks: int = 4) -> list[str]:
    normalized = user_input
    normalized = normalized.replace("\uff0c", ",").replace("\u3001", ",")
    normalized = normalized.replace("\uff1b", ";").replace("\u3002", ";")
    normalized = re.sub(
        r"(\u7136\u540e|\u63a5\u7740|\u6700\u540e|\u5e76\u4e14|\u540c\u65f6|\u53e6\u5916)",
        ";",
        normalized,
    )
    chunks = re.split(r"[\n;,]+", normalized)
    tasks: list[str] = []
    for chunk in chunks:
        segment = chunk.strip()
        if not segment:
            continue
        numbered_parts = re.split(r"(?:^|\s)(?:\d+[.)]\s+|[-*]\s+)", segment)
        extracted = [part.strip() for part in numbered_parts if part.strip()]
        if extracted:
            tasks.extend(extracted)
        else:
            tasks.append(segment)
    if not tasks:
        return [user_input.strip()]
    return tasks[:max_tasks]


def parse_supervisor_decision(content: str) -> tuple[bool, str, str] | None:
    text = str(content or "").strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    parsed: object
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        brace = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not brace:
            return None
        try:
            parsed = json.loads(brace.group(0))
        except json.JSONDecodeError:
            return None

    if not isinstance(parsed, dict):
        return None

    raw_continue = parsed.get("continue")
    if isinstance(raw_continue, bool):
        should_continue = raw_continue
    elif isinstance(raw_continue, str):
        normalized = raw_continue.strip().lower()
        should_continue = normalized in {"true", "yes", "y", "1", "continue"}
    else:
        should_continue = bool(raw_continue)

    next_focus_task = str(parsed.get("next_focus_task") or parsed.get("next_focus") or "").strip()
    reason = str(parsed.get("reason") or parsed.get("decision_reason") or "").strip()
    return should_continue, next_focus_task, reason


def fallback_supervisor_review_decision(
    *,
    user_input: str,
    reports: list[str],
    cycle: int,
    max_cycles: int,
) -> tuple[bool, str, str]:
    if cycle >= max_cycles:
        return False, "", "Reached max cycle limit."

    request = str(user_input or "").strip()
    latest = str(reports[-1] if reports else "").lower()
    complete_markers = ("final", "complete", "done", "conclusion", "最终", "结论", "已完成")
    unresolved_markers = ("todo", "unknown", "risk", "assumption", "待补充", "未知", "风险", "假设")

    if cycle < 2 and len(request) >= 24:
        return True, "补充约束条件、边界场景与验收标准。", "Fallback: run at least two cycles for non-trivial requests."
    if any(token in latest for token in unresolved_markers):
        return True, "针对未解决项继续补充可执行细节。", "Fallback: latest report indicates unresolved items."
    if any(token in latest for token in complete_markers):
        return False, "", "Fallback: latest report appears complete."
    return False, "", "Fallback: no strong signal to continue."
