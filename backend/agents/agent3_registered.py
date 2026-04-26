import json, os
from uagents import Context, Field, Model, Protocol
from uagents.experimental.chat_agent import ChatAgent, LLMConfig, LLMParams
from agent3_analytics import compute_analytics

agent = ChatAgent(
    name="analytics_agent",
    seed=os.getenv("AGENT3_SEED", "replace-with-agent3-seed"),
    port=8002, mailbox=True, network="testnet",
    llm_config=LLMConfig(
        provider="openai",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
        url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        parameters=LLMParams(),
    ),
)
print(f"Agent 3 address: {agent.address}")

proto = Protocol(name="AnalyticsProtocol", version="0.1.0")

class AnalyticsRequest(Model):
    profile_id: int = Field(description="Profile ID to compute analytics for")

class AnalyticsResponse(Model):
    success: bool
    summary: str = Field(description="Human-readable analytics summary")
    report: str = Field(description="Full JSON analytics report")
    error: str = Field(default="")

@proto.on_message(AnalyticsRequest, replies={AnalyticsResponse})
async def handle(ctx: Context, sender: str, msg: AnalyticsRequest):
    ctx.logger.info(f"Analytics request for profile {msg.profile_id}")
    try:
        result = compute_analytics(msg.profile_id)
        s = result.get("summary", {})
        ai = result.get("ai_insights", {})
        summary = (
            f"Analytics for profile {msg.profile_id}:\n"
            f"• Pitches sent: {s.get('total_pitches_sent', 0)}\n"
            f"• Response rate: {s.get('overall_response_rate', 0)}%\n"
            f"• Bookings: {s.get('total_bookings', 0)}\n"
            f"• Top insight: {ai.get('top_insight', 'Not enough data yet')}"
        )
        await ctx.send(sender, AnalyticsResponse(success=True, summary=summary, report=json.dumps(result)))
    except Exception as e:
        await ctx.send(sender, AnalyticsResponse(success=False, summary=str(e), report="{}", error=str(e)))

agent.include(proto, publish_manifest=True)
if __name__ == "__main__":
    agent.run()