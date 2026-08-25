"""Node functions for the LangGraph workflow.

Each function receives AgentState and returns a partial state update dict.
Do NOT mutate input state — return new values only.

LLM REQUIREMENT:
- classify_node MUST use a real LLM call (structured output for intent classification)
- answer_node MUST use a real LLM call (grounded response generation)
- evaluate_node SHOULD use LLM-as-judge (bonus points; heuristic acceptable for base score)
"""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from .llm import get_llm
from .state import AgentState, make_event


# ─── LLM STRUCTURED OUTPUT SCHEMA ────────────────────────────────────
class ClassificationResult(BaseModel):
    """Structured intent classification output."""

    route: Literal["simple", "tool", "missing_info", "risky", "error"] = Field(
        description="The classified route for the user query."
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        description=(
            "Risk level: 'high' for risky actions, 'medium' for error reports, "
            "'low' for lookups and simple questions."
        )
    )
    reasoning: str = Field(description="Short rationale for the classification.")


CLASSIFY_SYSTEM_PROMPT = """You are an expert intent classifier for support ticketing.
Classify the query into EXACTLY ONE of 5 routes based on priority:

Priority Order: risky > tool > missing_info > error > simple

1. 'risky' (Priority 1):
   - Actions with side-effects: refunds, deletions, cancellations, sending emails.
   - Examples: "Refund this customer", "Delete customer account after verification".
   - risk_level MUST be "high".

2. 'tool' (Priority 2):
   - Information lookups: order status, package tracking, query database records.
   - Examples: "Please lookup order status for order 12345", "Track package ABC".
   - risk_level is "low".

3. 'missing_info' (Priority 3):
   - Vague, ambiguous, incomplete queries lacking context.
   - Examples: "Can you fix it?", "Help me with this".
   - risk_level is "low".

4. 'error' (Priority 4):
   - System failure reports: timeouts, crashes, unrecoverable errors.
   - Examples: "Timeout failure while processing", "System failure cannot recover".
   - risk_level is "medium".

5. 'simple' (Priority 5):
   - General FAQ questions answerable without tools.
   - Examples: "How do I reset my password?", "What are your business hours?".
   - risk_level is "low".

Return the structured classification."""


ANSWER_SYSTEM_PROMPT = """You are a helpful, professional AI customer support agent.
Generate a concise, accurate response grounded in context (tool results, approval, query).
Do NOT invent facts not in context. Incorporate tool results and approval clearly."""


# ─── EXAMPLE: working node (provided for reference) ──────────────────
def intake_node(state: AgentState) -> dict:
    """Normalize raw query. This node is provided as a working example."""
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }


# ─── TV2 NODES IMPLEMENTATION ────────────────────────────────────────


def classify_node(state: AgentState) -> dict:
    """Classify the query into a route using an LLM.

    *** MUST use a real LLM call — keyword-only heuristics will lose points. ***

    Use .with_structured_output() to get reliable enum classification.
    The LLM classifies into one of: simple, tool, missing_info, risky, error.
    """
    query = state.get("query", "").strip()
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ClassificationResult)

    messages = [
        SystemMessage(content=CLASSIFY_SYSTEM_PROMPT),
        HumanMessage(content=f"User Query: {query}"),
    ]
    result: ClassificationResult = structured_llm.invoke(messages)

    route = result.route
    risk_level = "high" if route == "risky" else result.risk_level

    return {
        "route": route,
        "risk_level": risk_level,
        "events": [
            make_event(
                "classify",
                "completed",
                f"classified as {route}",
                route=route,
                risk_level=risk_level,
                reasoning=result.reasoning,
            )
        ],
    }


def tool_node(state: AgentState) -> dict:
    """Execute a mock tool call.

    Simulate transient failures for error-route scenarios to test retry loops.

    Requirements:
    - Read current attempt count from state
    - If route is "error" and attempt < 2: return error result (string containing "ERROR")
    - Otherwise: return a mock success result string
    - Append result to tool_results list

    Return: {"tool_results": [result_string], "events": [make_event(...)]}
    """
    raise NotImplementedError("TODO(student): implement mock tool with error simulation")


def evaluate_node(state: AgentState) -> dict:
    """Evaluate tool results — the retry-loop gate.

    Check whether the latest tool result is satisfactory or needs retry.

    SHOULD use LLM-as-judge for bonus points. Heuristic (e.g., check for "ERROR" substring)
    is acceptable for base score.

    Requirements:
    - Read the latest entry from tool_results
    - Set evaluation_result to "needs_retry" or "success"
    - This field drives route_after_evaluate conditional edge

    Note: You may need to add 'evaluation_result' to AgentState if not present.

    Return: {"evaluation_result": str, "events": [make_event(...)]}
    """
    raise NotImplementedError("TODO(student): implement tool result evaluation")


def answer_node(state: AgentState) -> dict:
    """Generate a final response using an LLM.

    *** MUST use a real LLM call — hardcoded strings will lose points. ***

    The LLM generates a helpful response grounded in available context:
    - tool_results (if any)
    - approval decision (if risky route)
    - original query
    """
    query = state.get("query", "").strip()
    tool_results = state.get("tool_results", [])
    approval = state.get("approval")
    proposed_action = state.get("proposed_action")

    context_parts: list[str] = [f"Original Query: {query}"]
    if tool_results:
        context_parts.append("Tool Execution Results:\n" + "\n".join(tool_results))
    if proposed_action:
        context_parts.append(f"Proposed Action: {proposed_action}")
    if approval:
        status_str = "Approved" if approval.get("approved") else "Rejected"
        context_parts.append(
            f"Approval Decision: {status_str} by {approval.get('reviewer', 'reviewer')}. "
            f"Comment: {approval.get('comment', '')}"
        )

    context_text = "\n\n".join(context_parts)
    llm = get_llm(temperature=0.0)
    prompt_content = (
        f"Context:\n{context_text}\n\n"
        "Please generate the final customer support answer:"
    )
    messages = [
        SystemMessage(content=ANSWER_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content),
    ]
    response = llm.invoke(messages)
    final_answer = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "final_answer": final_answer.strip(),
        "events": [make_event("answer", "completed", "final answer generated")],
    }


def ask_clarification_node(state: AgentState) -> dict:
    """Ask for missing information instead of hallucinating.

    Generate a specific clarification question based on the vague/incomplete query.
    """
    query = state.get("query", "").strip()
    approval = state.get("approval")

    if approval and not approval.get("approved", True):
        comment = approval.get("comment", "Action was not approved by reviewer.")
        clarification = (
            f"Yêu cầu của bạn không thể thực hiện vì chưa được phê duyệt: {comment}. "
            "Bạn có muốn đưa ra giải pháp thay thế nào không?"
        )
    else:
        clarification = (
            f"Tôi rất muốn hỗ trợ bạn, nhưng yêu cầu '{query}' hiện đang thiếu thông tin cụ thể. "
            "Bạn vui lòng cung cấp thêm chi tiết (mã đơn, tài khoản hoặc mô tả sự cố) để xử lý nhé?"
        )

    return {
        "pending_question": clarification,
        "final_answer": clarification,
        "events": [make_event("clarify", "completed", "requested clarification")],
    }


def risky_action_node(state: AgentState) -> dict:
    """Prepare a risky action for human approval.

    Describe the proposed action and why it requires approval.
    """
    query = state.get("query", "").strip()
    risk_level = state.get("risk_level", "high")
    proposed_action = (
        f"Proposed action: '{query}'. This action has side effects "
        f"(risk_level={risk_level}) and requires human approval before execution."
    )

    return {
        "proposed_action": proposed_action,
        "events": [
            make_event(
                "risky_action",
                "completed",
                "proposed action prepared for approval",
                risk_level=risk_level,
            )
        ],
    }


def approval_node(state: AgentState) -> dict:
    """Human-in-the-loop approval step.

    Default behavior: mock approval (approved=True) so tests and CI run offline.
    Extension: if env LANGGRAPH_INTERRUPT=true, use langgraph.types.interrupt() for real HITL.
    """
    proposed_action = state.get("proposed_action", "")

    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() == "true":
        decision = interrupt(
            {"proposed_action": proposed_action, "message": "Approve this action?"}
        )
        approval = {
            "approved": bool(decision.get("approved", False)),
            "reviewer": decision.get("reviewer", "human-reviewer"),
            "comment": decision.get("comment", ""),
        }
    else:
        approval = {
            "approved": True,
            "reviewer": "mock-reviewer",
            "comment": "auto-approved for offline run",
        }

    return {
        "approval": approval,
        "events": [
            make_event(
                "approval",
                "completed",
                f"approval decision: approved={approval['approved']}",
                **approval,
            )
        ],
    }


def retry_or_fallback_node(state: AgentState) -> dict:
    """Record a retry attempt.

    Increment the attempt counter and log the transient failure.

    Requirements:
    - Read current attempt from state, increment by 1
    - Add an error message to errors list
    - Return updated attempt count

    Return: {"attempt": int, "errors": [str], "events": [make_event(...)]}
    """
    raise NotImplementedError("TODO(student): implement retry with attempt tracking")


def dead_letter_node(state: AgentState) -> dict:
    """Handle unresolvable failures after max retries exceeded.

    This is the third layer: retry → fallback → dead letter.
    Log the failure and set a final_answer explaining that the request could not be completed.

    Return: {"final_answer": str, "events": [make_event(...)]}
    """
    raise NotImplementedError("TODO(student): implement dead letter handling")


def finalize_node(state: AgentState) -> dict:
    """Emit a final audit event. All routes must pass through here before END.

    Return: {"events": [make_event("finalize", "completed", "workflow finished")]}
    """
    raise NotImplementedError("TODO(student): implement finalize node")
