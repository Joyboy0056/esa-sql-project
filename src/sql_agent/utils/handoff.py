from pydantic import BaseModel
from agents import RunContextWrapper

from src.sql_agent.context import SQLContext

# Handoff aux defs
class SQLReport(BaseModel):
    report: str

async def log_handoff(ctx: RunContextWrapper[SQLContext], input_data: SQLReport):
    # print(f"Handoff call with input: {input_data.report}")
    # print("Input tokens: ", ctx.usage.input_tokens)
    # print("Output tokens: ", ctx.usage.output_tokens)
    pass