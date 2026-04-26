import json, os
from uagents import Context, Field, Model, Protocol
from uagents.experimental.chat_agent import ChatAgent, LLMConfig, LLMParams
from agent1_market_research import run_market_research

agent = ChatAgent(
    name="market_research_agent",
    seed=os.getenv("AGENT1_SEED", "replace-with-agent1-seed"),
    port=8000, mailbox=True, network="testnet",
    llm_config=LLMConfig(
        provider="openai",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
        url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        parameters=LLMParams(),
    ),
)
print(f"Agent 1 address: {agent.address}")

proto = Protocol(name="MarketResearchProtocol", version="0.1.0")

class EntertainerProfile(Model):
    name: str = Field(description="Entertainer's name")
    entertainer_type: str = Field(description="e.g. comedian, rapper, singer, dj")
    genre_style: str = Field(default="General")
    experience_years: int = Field(default=0)
    shows_count: int = Field(default=0)
    location: str = Field(default="Los Angeles, CA")
    touring_region: str = Field(default="Regional")
    rate_min: int = Field(default=0)
    rate_max: int = Field(default=0)
    instagram_followers: int = Field(default=0)
    bio: str = Field(default="")

class MarketResearchResponse(Model):
    success: bool
    summary: str = Field(description="Human-readable summary")
    report: str = Field(description="Full JSON report")
    error: str = Field(default="")

@proto.on_message(EntertainerProfile, replies={MarketResearchResponse})
async def handle(ctx: Context, sender: str, msg: EntertainerProfile):
    ctx.logger.info(f"Research request: {msg.name} ({msg.entertainer_type})")
    try:
        result = run_market_research(msg.dict())
        insights = result.get("market_insights", {})
        summary = (
            f"Market research for {msg.name} ({msg.entertainer_type.title()}):\n"
            f"• Tier: {insights.get('experience_tier','N/A').replace('_',' ').title()}\n"
            f"• Recommended rate: ${insights.get('recommended_rate_min')}–${insights.get('recommended_rate_max')}/show\n"
            f"• Top action: {result.get('action_items', ['N/A'])[0]}"
        )
        await ctx.send(sender, MarketResearchResponse(success=True, summary=summary, report=json.dumps(result)))
    except Exception as e:
        await ctx.send(sender, MarketResearchResponse(success=False, summary=str(e), report="{}", error=str(e)))

agent.include(proto, publish_manifest=True)
if __name__ == "__main__":
    agent.run()