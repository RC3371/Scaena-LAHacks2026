import json, os
from uagents import Context, Field, Model, Protocol
from uagents.experimental.chat_agent import ChatAgent, LLMConfig, LLMParams
from agent2_pitch_generator import generate_pitch

agent = ChatAgent(
    name="pitching_agent",
    seed=os.getenv("AGENT2_SEED", "replace-with-agent2-seed"),
    port=8001, mailbox=True, network="testnet",
    llm_config=LLMConfig(
        provider="openai",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
        url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        parameters=LLMParams(),
    ),
)
print(f"Agent 2 address: {agent.address}")

proto = Protocol(name="PitchingProtocol", version="0.1.0")

class PitchRequest(Model):
    profile: str = Field(description="JSON string of entertainer profile")
    prospect: str = Field(description="JSON string of venue/prospect")
    proposed_rate: float = Field(description="Proposed rate in USD")

class PitchResponse(Model):
    success: bool
    subject: str = Field(default="")
    body: str = Field(default="")
    key_angle: str = Field(default="")
    error: str = Field(default="")

@proto.on_message(PitchRequest, replies={PitchResponse})
async def handle(ctx: Context, sender: str, msg: PitchRequest):
    ctx.logger.info(f"Pitch request received")
    try:
        profile = json.loads(msg.profile)
        prospect = json.loads(msg.prospect)
        result = generate_pitch(profile, prospect, msg.proposed_rate)
        await ctx.send(sender, PitchResponse(
            success=True,
            subject=result.get("subject", ""),
            body=result.get("body", ""),
            key_angle=result.get("key_angle", ""),
        ))
    except Exception as e:
        await ctx.send(sender, PitchResponse(success=False, error=str(e)))

agent.include(proto, publish_manifest=True)
if __name__ == "__main__":
    agent.run()