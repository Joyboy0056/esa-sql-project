from typing import Any, Generic, TypeVar
from agents import Agent
from .base_context import BaseContext

TContext = TypeVar("TContext", bound=BaseContext)


class ESAAgent(Generic[TContext]):
    def __init__(self, agent: Agent[Any], context=None):
        self.agent = agent
        self.context = context

    def __getattr__(self, attr):
        """Delegate attributes not found in this Agent class to the wrapped agent"""
        return getattr(self.agent, attr)