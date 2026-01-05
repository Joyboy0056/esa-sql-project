from agents import Agent, handoff, ModelSettings
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from src.sql_agent.prompts import EXECUTOR_PROMPT, COLLECTOR_PROMPT
from src.sql_agent.tools import (
    getMetadata,
    retrieveQueries,
    executeQuery
)
from src.sql_agent.utils.handoff import log_handoff, SQLReport
from build.config import config

# Sub agent
executor = Agent(
    name="Executor",
    instructions=EXECUTOR_PROMPT,
    tools=[executeQuery],
    handoff_description="Agent that runs PostgreSQL query on database",
    model=config.MODEL,
    model_settings=ModelSettings(tool_choice="required") # always execute queries
)

executor_handoff = handoff(
    agent=executor, 
    on_handoff=log_handoff, 
    input_type=SQLReport,
    # input_filter=
)

# Agent
collector = Agent(
    name="Galileo",
    instructions=prompt_with_handoff_instructions(COLLECTOR_PROMPT),
    tools=[
        retrieveQueries,
        getMetadata, 
    ],
    handoffs=[executor_handoff,],
    handoff_description="Agent that explores db and collects useful data for writing a SQL query",
    model=config.MODEL,
)