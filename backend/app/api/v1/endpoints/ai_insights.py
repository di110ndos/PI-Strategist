"""AI Insights endpoint using the AIAdvisor."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

# Ensure src/ is importable (editable install preferred: `pip install -e .`)
src_path = str(Path(__file__).parent.parent.parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

router = APIRouter()


class InsightsRequest(BaseModel):
    """Request model for AI insights."""

    pi_analysis: Dict[str, Any]
    capacity_plan: Optional[Dict[str, Any]] = None
    red_flags: Optional[List[Dict[str, Any]]] = None
    insight_type: str = "full"  # "full" | "summary" | "rebalancing"


class RecommendationResponse(BaseModel):
    category: str
    priority: str
    title: str
    description: str
    action_items: List[str] = []
    impact: str = ""
    affected_resources: List[str] = []
    affected_sprints: List[str] = []


class RebalancingSuggestion(BaseModel):
    action: str
    reason: str = ""
    priority: str = "medium"
    impact: str = ""


class InsightsResponse(BaseModel):
    """Response model for AI insights."""

    executive_summary: str = ""
    recommendations: List[RecommendationResponse] = []
    risk_assessment: str = ""
    optimization_opportunities: List[str] = []
    key_metrics_commentary: str = ""
    rebalancing_suggestions: List[RebalancingSuggestion] = []


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    pi_analysis: Dict[str, Any]
    capacity_plan: Optional[Dict[str, Any]] = None
    previous_insights: Optional[Dict[str, Any]] = None
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str


class _DictProxy:
    """Wraps a dict to allow attribute-style access, compatible with AIAdvisor."""

    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)
        if name not in self._data:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        val = self._data[name]
        if isinstance(val, dict):
            return _DictProxy(val)
        if isinstance(val, list):
            return [_DictProxy(v) if isinstance(v, dict) else v for v in val]
        return val

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def items(self):
        return {k: _DictProxy(v) if isinstance(v, dict) else v for k, v in self._data.items()}.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return [_DictProxy(v) if isinstance(v, dict) else v for v in self._data.values()]

    def get(self, key, default=None):
        val = self._data.get(key, default)
        if isinstance(val, dict):
            return _DictProxy(val)
        return val


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest):
    """Generate AI-powered insights for PI analysis data."""

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file or configure it in Settings.",
        )

    try:
        from pi_strategist.analyzers.ai_advisor import AIAdvisor

        advisor = AIAdvisor(api_key=settings.anthropic_api_key)

        if not advisor.is_available:
            raise HTTPException(
                status_code=400,
                detail="AI features not available. Ensure the anthropic package is installed.",
            )

        pi_proxy = _DictProxy(request.pi_analysis)

        capacity_proxy = _DictProxy(request.capacity_plan) if request.capacity_plan else None

        if request.insight_type == "summary":
            summary_text = advisor.generate_executive_summary(pi_proxy, capacity_proxy)
            return InsightsResponse(executive_summary=summary_text)

        if request.insight_type == "rebalancing":
            raw_suggestions = advisor.suggest_rebalancing(pi_proxy, capacity_proxy)
            suggestions = []
            for item in raw_suggestions:
                if "error" in item:
                    suggestions.append(RebalancingSuggestion(
                        action=f"Error: {item['error']}",
                        priority="low",
                    ))
                elif "suggestion" in item:
                    suggestions.append(RebalancingSuggestion(
                        action=item["suggestion"],
                        priority="low",
                    ))
                else:
                    suggestions.append(RebalancingSuggestion(
                        action=item.get("action", ""),
                        reason=item.get("reason", ""),
                        priority=item.get("priority", "medium"),
                        impact=item.get("impact", ""),
                    ))
            return InsightsResponse(rebalancing_suggestions=suggestions)

        # Full analysis
        result = advisor.analyze_pi_planning(
            pi_proxy,
            capacity_proxy,
            request.red_flags,
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        return InsightsResponse(
            executive_summary=result.executive_summary,
            recommendations=[
                RecommendationResponse(
                    category=rec.category,
                    priority=rec.priority,
                    title=rec.title,
                    description=rec.description,
                    action_items=rec.action_items,
                    impact=rec.impact,
                    affected_resources=rec.affected_resources,
                    affected_sprints=rec.affected_sprints,
                )
                for rec in result.recommendations
            ],
            risk_assessment=result.risk_assessment,
            optimization_opportunities=result.optimization_opportunities,
            key_metrics_commentary=result.key_metrics_commentary,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Sanitize: never leak the API key in error responses
        if settings.anthropic_api_key:
            error_msg = error_msg.replace(settings.anthropic_api_key, "***")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {error_msg}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Follow-up chat about AI analysis results."""

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file.",
        )

    try:
        from pi_strategist.analyzers.ai_advisor import AIAdvisor

        advisor = AIAdvisor(api_key=settings.anthropic_api_key)

        if not advisor.is_available:
            raise HTTPException(
                status_code=400,
                detail="AI features not available. Ensure the anthropic package is installed.",
            )

        pi_proxy = _DictProxy(request.pi_analysis)
        capacity_proxy = _DictProxy(request.capacity_plan) if request.capacity_plan else None

        # Build analysis context
        context = advisor._build_analysis_context(pi_proxy, capacity_proxy, None)

        # Include truncated previous insights if available
        insights_context = ""
        if request.previous_insights:
            insights_json = json.dumps(request.previous_insights, default=str)
            if len(insights_json) > 3000:
                insights_json = insights_json[:3000] + "..."
            insights_context = f"\n\nPrevious AI Analysis Results:\n{insights_json}"

        system_preamble = f"""You are an expert PI Planning advisor assisting project managers and account managers. The user is asking follow-up questions about their PI analysis data.

Here is the analysis data for context:
{context}{insights_context}

Answer the user's question based on this data. Tailor your responses for a PM/account manager audience:
- Focus on delivery risk, timeline impacts, and client-facing concerns
- Highlight budget and staffing implications with specific numbers
- Frame recommendations as stakeholder-ready talking points
- Call out dependencies and blockers that affect commitments
- Keep responses concise and actionable"""

        # Build messages: system preamble as first user message, then conversation history
        messages = [{"role": "user", "content": system_preamble}]
        messages.append({"role": "assistant", "content": "I have the PI analysis data loaded. What would you like to know?"})

        # Append last 5 exchanges from conversation history
        history = request.conversation_history[-10:]  # 5 exchanges = 10 messages
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Append the current question
        messages.append({"role": "user", "content": request.question})

        client = advisor._get_client()
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            messages=messages,
        )

        return ChatResponse(answer=response.content[0].text)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if settings.anthropic_api_key:
            error_msg = error_msg.replace(settings.anthropic_api_key, "***")
        raise HTTPException(status_code=500, detail=f"Chat failed: {error_msg}")
