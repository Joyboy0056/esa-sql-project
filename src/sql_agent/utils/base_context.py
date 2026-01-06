from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseContext(ABC):
    """Abstract base class for handling context of AI agents"""
    _sent_to_model: dict = field(default_factory=dict, init=False, repr=False)
    _turn: int = 0

    @abstractmethod
    def get_delta_for_model(self, *args, **kwargs) -> dict:
        """Compute new fields or update them with respect to `_sent_to_model`"""
        pass

    @abstractmethod
    def to_json(self, obj: Any):
        """Convert the `delta_dict` to json for for appending it to model's input items"""
        pass