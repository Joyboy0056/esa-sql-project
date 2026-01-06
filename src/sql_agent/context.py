from dataclasses import dataclass, field
from typing import List, Dict, Any, Iterable
import re
import json
from decimal import Decimal
from datetime import date, datetime

from src.sql_agent.utils.base_context import BaseContext


@dataclass
class SQLContext(BaseContext):
    user_queries: List[str] = field(default_factory=list)
    retrieved_queries: List[Dict[str, Any]] = field(default_factory=list)
    metadata: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[List[Dict[str, Any]]] = field(default_factory=list)
    executed_sql_queries: List[str] = field(default_factory=list)

    # General attributes
    _field_order = [
        "user_queries",
        "retrieved_queries",
        "metadata",
        "notes",
        "executed_sql_queries",
    ]

    # Pattern for similar queries parsing
    _similar_query_pattern: re.Pattern = re.compile(
        r'NL key:\s*(.*?)\s*\nSQL value:\s*(.*?)\s*\nScore:\s*(\d+\.?\d*)',
        re.DOTALL | re.IGNORECASE
    )

    # CTX METHODS
    def append_retrieved_query(self, queries_string: str) -> None:
        """Parse and append retrieved queries"""

        parsed = [
            {
                "nl": nl.strip(),
                "sql": ' '.join(sql.split()),
                "score": float(score)
            }
            for nl, sql, score in self._similar_query_pattern.findall(queries_string)
        ]

        self.retrieved_queries.extend(parsed)

    
    def append_note(self, note: str) -> None:
        """Interpret model output as json-string and append it as python obj"""
        if not note or not note.strip():
            return
        
        try:
            parsed = json.loads()
        
        except json.JSONDecodeError:
            parsed = note.strip()

        self.notes.append(parsed)

    
    def append_executed_sql_query(self, sql_query_string: str) -> None:
        """Append and parse last executed query"""
        if sql_query_string.strip():
            normalized = ' '.join(sql_query_string.split())
            self.executed_sql_queries.append(normalized)
        
        else:
            raise

    
    # __DUNDERS__
    # Handling ctx object iterability
    def __iter__(self):
        """Make an object `SQLContext` iterable via for loop"""
        for field_name in self._field_order:
            yield field_name, getattr(self, field_name)

    def iter_fields(self, *, exclude: Iterable[str]=()):
        """Iterate on fields excluding the specified ones - custom loop"""
        exclude = set(exclude)
        for field_name in self._field_order:
            if field_name not in exclude:
                yield field_name, getattr(self, field_name)

    def to_dict(self, *, exclude: Iterable[str]=()) -> dict:
        """Return a filtered dict of fields"""
        return {k: v for k, v in self.iter_fields(exclude=exclude)}
    
    
    def __str__(self) -> str:
        """Readable string repr for `SQLContext` object"""
        lines = ["SQLContext:"]
        for field_name, value in self:
            if isinstance(value, (list, set)):
                lines.append(f"  {field_name}: ({len(value)} items)")
            else:
                lines.append(f"  {field_name}: {value}")
        return "\n".join(lines)
    

    # ABS METHODS
    def get_delta_for_model(self, exclude: Iterable[str]=["user_queries"]):
        """Return new or updated fields with respect to `_sent_to_model`.
           Update `_sent_to_model` with no duplicates on context.

           Args:
                exclude: Field to exclude from delta
        """
        delta = {}

        for key, value in self.iter_fields(exclude=exclude):
            prev = self._sent_to_model.get(key)

            if isinstance(value, set):
                new_items = value - (prev if prev else set())
                if new_items:
                    delta[key] = new_items
                    self._sent_to_model[key] = value.copy()
                elif isinstance(value, list):
                    new_items = [v for v in value if not prev or v not in prev]
                    if new_items:
                        delta[key] = new_items
                        self._sent_to_model[key] = value.copy()
                else:
                    if value != prev:
                        delta[key] = value
                        self._sent_to_model[key] = value
        
        return delta
    
    def to_json(self, obj: Any=None) -> str:
        """JSON format handling for AI models"""
        def _convert(o: Any) -> Any:
            """Convert python obj in valid JSON for model, handling nested types"""
            if isinstance(o, set):
                return list(o)
            elif isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            elif isinstance(o, list):
                return [_convert(v) for v in o]
            elif isinstance(o, Decimal):
                return float(o)
            elif isinstance(o, (datetime, date)):
                return o.isoformat()
            else: 
                return o
        return json.dumps(_convert(obj if obj is not None else self.to_dict()))