# usage: uv run -m chainlit run scripts/ui.py -w
import re
import chainlit as cl
from agents import set_tracing_disabled
set_tracing_disabled(disabled=True)
from agents.exceptions import MaxTurnsExceeded

from src.sql_agent.agent import collector as galileo
from src.sql_agent.utils.repl import AgentRunner
from src.logger import logger


@cl.on_chat_start
async def start():
    agent = galileo
    cl.user_session.set("agent", agent)

    await cl.Message(
        content="## Hello there! 🌍"
                "\n\n> Here's Galileo, a specialized `SQL-Agent` for Earth Observation databases. Think of me as your translator between human curiosity and satellite data."  
                "\n\n#### What'd you like to discover? 🛰️"
    ).send()


@cl.on_message
async def main(message: cl.Message):

    # Images handling
    THUMBNAIL_REGEX = re.compile(
        r"(?<!!\[\]\()https:\/\/datahub\.creodias\.eu\/odata\/v1\/Assets\([^)]+\)\/\$value"
    )

    def _embed_thumbnails(text: str) -> str:
        """
        Converte tutti i link thumbnail CREODIAS in Markdown image embeds.
        """
        return THUMBNAIL_REGEX.sub(lambda m: f"![]({m.group(0)})", text)

    try:
        agent = cl.user_session.get("agent")
        runner = AgentRunner(starting_agent=agent)
        
        logger.info(f"Starting agent run for: {message.content}")
        
        # Messaggio temporaneo per gli eventi
        status_msg = cl.Message(content="🔭 Starting analysis...", author="Galileo")
        await status_msg.send()
        
        final_response = ""
        
        async for event in runner.run_demo_loop(ui=True, user_q=message.content):
            if event.type == "agent_switch":
                if event.content == "Galileo":
                    status_msg.content = f"🔭 `{event.content}` is looking at the sky..."
                elif event.content == "Executor":
                    status_msg.content = f"🤖 `Galileo` is querying the database..."
                await status_msg.update()
                
            elif event.type == "tool_call":
                status_msg.content = f"🔧 {event.content}"
                await status_msg.update()
                
            elif event.type == "final":
                final_response = _embed_thumbnails(event.content)
        
        # Rimuovi il messaggio di stato
        await status_msg.remove()
        
        # Messaggio finale pulito
        final_msg = cl.Message(content="", author="🛰️ Galileo")
        await final_msg.send()
        
        for char in final_response:
            await final_msg.stream_token(char)
        
        await final_msg.update()
    
    except MaxTurnsExceeded:
        logger.error("Max turn exceeded (10).")