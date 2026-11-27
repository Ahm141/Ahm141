import os
from dotenv import load_dotenv
load_dotenv()

from livekit.agents import Agent, AgentSession, JobContext, RunContext, WorkerOptions, cli, function_tool
from livekit.agents.llm import ChatContext
from livekit.plugins import google
import core

print(">>> NEW AGENT FILE:", __file__)

SESSION = "voice"


class Secretary(Agent):
    def __init__(self, chat_ctx: ChatContext):
        super().__init__(instructions=core.system_prompt(), chat_ctx=chat_ctx)

    @function_tool
    async def add_appointment(self, context: RunContext, title: str, date: str, time: str, notes: str = "") -> str:
        """سجّل موعد جديد. date بصيغة YYYY-MM-DD و time بصيغة 24 ساعة HH:MM."""
        return core.add_appointment.invoke({"title": title, "date": date, "time": time, "notes": notes})

    @function_tool
    async def list_appointments(self, context: RunContext, date: str = "") -> str:
        """اعرض المواعيد الفعالة. اترك date فارغ لعرض كل المواعيد القادمة."""
        return core.list_appointments.invoke({"date": date})

    @function_tool
    async def cancel_appointment(self, context: RunContext, appointment_id: int) -> str:
        """الغِ موعد حسب رقمه."""
        return core.cancel_appointment.invoke({"appointment_id": appointment_id})


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    print(">>> NEW ENTRYPOINT RUNNING")

    kwargs = {"voice": os.getenv("GEMINI_VOICE", "Aoede"), "temperature": 0.8}
    if os.getenv("GEMINI_LIVE_MODEL"):
        kwargs["model"] = os.getenv("GEMINI_LIVE_MODEL")
    session = AgentSession(llm=google.realtime.RealtimeModel(**kwargs))

    @session.on("conversation_item_added")
    def _saved(ev):
        it = ev.item
        if it.role in ("user", "assistant") and it.text_content:
            core.save(SESSION, it.role, it.text_content)

    hist = ChatContext()
    for role, content in core.history(SESSION):
        hist.add_message(role=role, content=content)

    await session.start(agent=Secretary(hist), room=ctx.room)
    await session.generate_reply(instructions="رحبي بأحمد بجملة قصيرة وعفوية وسأليه شنو يريد.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="noor"))