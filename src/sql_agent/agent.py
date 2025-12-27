from agents import Agent, handoff, ModelSettings
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from src.sql_agent.prompts import executor_prompt, collector_prompt
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
    instructions=executor_prompt,
    tools=[executeQuery],
    handoff_description="Agente che esegue query sqlite su db",
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
    instructions=prompt_with_handoff_instructions(collector_prompt),
    tools=[getMetadata, retrieveQueries],
    handoffs=[executor_handoff,],
    handoff_description="Agente che esplora il db per raccogliere dati utili per scrivere una query sqlite",
    model=config.MODEL,
)