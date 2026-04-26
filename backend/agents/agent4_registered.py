import json, os
from uagents import Context, Field, Model, Protocol
from uagents.experimental.chat_agent import ChatAgent, LLMConfig, LLMParams
from agent4_followup import generate_followup_message, generate_objection_response

agent = ChatAgent(
    name="followup_agent",
    seed=os.getenv("AGENT4_SEED", "replace-with-agent4-seed"),
    port=8003, mailbox=True, network="testnet",
    llm_config=LLMConfig(
        provider="openai",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
        url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        parameters=LLMParams(),
    ),
)
print(f"Agent 4 address: {agent.address}")

proto = Protocol(name="FollowUpProtocol", version="0.1.0")

class FollowUpRequest(Model):
    profile: str = Field(description="JSON string of entertainer profile")
    prospect: str = Field(description="JSON string of prospect/venue")
    original_pitch: str = Field(description="JSON string of the original pitch")
    sequence_number: int = Field(description="Follow-up number: 1, 2, or 3")

class ObjectionRequest(Model):
    profile: str = Field(description="JSON string of entertainer profile")
    prospect: str = Field(description="JSON string of prospect/venue")
    objection_type: str = Field(description="e.g. too_expensive, not_available, not_right_fit")
    objection_text: str = Field(description="The actual objection text from the venue")
    original_rate: float = Field(description="Original proposed rate in USD")

class FollowUpResponse(Model):
    success: bool
    subject: str = Field(default="")
    body: str = Field(default="")
    angle_used: str = Field(default="")
    error: str = Field(default="")

@proto.on_message(FollowUpRequest, replies={FollowUpResponse})
async def handle_followup(ctx: Context, sender: str, msg: FollowUpRequest):
    ctx.logger.info(f"Follow-up #{msg.sequence_number} request")
    try:
        result = generate_followup_message(
            json.loads(msg.profile),
            json.loads(msg.prospect),
            json.loads(msg.original_pitch),
            msg.sequence_number,
        )
        await ctx.send(sender, FollowUpResponse(
            success=True,
            subject=result.get("subject", ""),
            body=result.get("body", ""),
            angle_used=result.get("angle_used", ""),
        ))
    except Exception as e:
        await ctx.send(sender, FollowUpResponse(success=False, error=str(e)))

@proto.on_message(ObjectionRequest, replies={FollowUpResponse})
async def handle_objection(ctx: Context, sender: str, msg: ObjectionRequest):
    ctx.logger.info(f"Objection handling request: {msg.objection_type}")
    try:
        result = generate_objection_response(
            json.loads(msg.profile),
            json.loads(msg.prospect),
            msg.objection_type,
            msg.objection_text,
            msg.original_rate,
        )
        best = result.get("counter_offers", [{}])[0]
        await ctx.send(sender, FollowUpResponse(
            success=True,
            subject=best.get("subject", ""),
            body=best.get("body", ""),
            angle_used=result.get("recommended_strategy", ""),
        ))
    except Exception as e:
        await ctx.send(sender, FollowUpResponse(success=False, error=str(e)))

agent.include(proto, publish_manifest=True)
if __name__ == "__main__":
    agent.run()