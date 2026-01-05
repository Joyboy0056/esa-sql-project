from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Literal, Set

from agents import Agent, Runner, RunHooks
from agents.result import RunResultStreaming
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from agents.stream_events import (
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    AgentUpdatedStreamEvent,
)
from agents.items import ItemHelpers


# ------ COLORS ------
class bcolors:
    # Colori di base
    BLACK = '\033[30m'
    DARK_GREY = '\033[90m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    PURPLE = '\033[38;5;129m'
    MIDNIGHT_BLUE = '\033[38;5;17m'
    # DARK_YELLOW
    BORDEAUX = '\033[38;5;52m'
    
    # Colori brillanti
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Colori dark/attenuati (usando DIM + colori base)
    DARK_RED = '\033[2;31m'
    DARK_GREEN = '\033[2;32m'
    DARK_YELLOW = '\033[2;33m'
    DARK_BLUE = '\033[2;34m'
    DARK_MAGENTA = '\033[2;35m'
    DARK_CYAN = '\033[2;36m'
    DARK_WHITE = '\033[2;37m'
    DARK_GRAY = '\033[2;90m'
    
    # Colori 256-color per tonalità più scure
    DARK_RED_256 = '\033[38;5;52m'      # Rosso scuro
    DARK_GREEN_256 = '\033[38;5;22m'    # Verde scuro
    DARK_BLUE_256 = '\033[38;5;18m'     # Blu scuro
    DARK_YELLOW_256 = '\033[38;5;94m'   # Giallo scuro/marrone
    DARK_CYAN_256 = '\033[38;5;23m'     # Ciano scuro
    DARK_MAGENTA_256 = '\033[38;5;53m'  # Magenta scuro
    DARK_GRAY_256 = '\033[38;5;236m'    # Grigio scuro
    CHARCOAL = '\033[38;5;240m'         # Carbone
    SLATE = '\033[38;5;244m'            # Ardesia
    
    # Stili
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    ENDC = '\033[0m'  # End color
    RESET = '\033[0m'
    
    # Sfondi
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Metodi helper
    @classmethod
    def colored(cls, text, color):
        """Restituisce testo colorato"""
        return f"{color}{text}{cls.ENDC}"
    
    @classmethod
    def success(cls, text):
        """Testo verde per successi"""
        return f"{cls.BRIGHT_GREEN}{text}{cls.ENDC}"
    
    @classmethod
    def error(cls, text):
        """Testo rosso per errori"""
        return f"{cls.BRIGHT_RED}{text}{cls.ENDC}"
    
    @classmethod
    def warning(cls, text):
        """Testo giallo per warning"""
        return f"{cls.BRIGHT_YELLOW}{text}{cls.ENDC}"
    
    @classmethod
    def info(cls, text):
        """Testo blu per info"""
        return f"{cls.BRIGHT_BLUE}{text}{cls.ENDC}"
    
    @classmethod
    def header(cls, text):
        """Testo magenta bold per header"""
        return f"{cls.BOLD}{cls.BRIGHT_MAGENTA}{text}{cls.ENDC}"
    
    @classmethod
    def dark_success(cls, text):
        """Testo verde scuro per successi discreti"""
        return f"{cls.DARK_GREEN_256}{text}{cls.ENDC}"
    
    @classmethod
    def dark_error(cls, text):
        """Testo rosso scuro per errori discreti"""
        return f"{cls.DARK_RED_256}{text}{cls.ENDC}"
    
    @classmethod
    def dark_warning(cls, text):
        """Testo giallo scuro per warning discreti"""
        return f"{cls.DARK_YELLOW_256}{text}{cls.ENDC}"
    
    @classmethod
    def dark_info(cls, text):
        """Testo blu scuro per info discrete"""
        return f"{cls.DARK_BLUE_256}{text}{cls.ENDC}"
    
    @classmethod
    def muted(cls, text):
        """Testo grigio scuro per testi secondari"""
        return f"{cls.DARK_GRAY_256}{text}{cls.ENDC}"


# ------ TYPES & MODES ------
InputDataMode = Literal[
    "tool",
    "handoff",
    "tool_and_handoff",
    "nothing_else",
]

EXIT_COMMANDS: Set[str] = {"exit", "quit", "stop", "cl"}

ReplEventType = Literal[
        "text_delta",
        "message",
        "tool_call",
        "tool_output",
        "agent_switch",
        "final",
    ]

@dataclass
class ReplEvent:
    type: ReplEventType
    content: str


# ------ AGENT RUNNER ------
class AgentRunner:
    """
    Stateful async runner for OpenAI Agents.
    """

    def __init__(
        self,
        starting_agent: Agent[Any],
        *,
        hooks: RunHooks | None = None,
        input_data_custom: InputDataMode = "nothing_else",
        enable_cli_prints: bool = True,
    ):
        self.agent = starting_agent
        self.hooks = hooks
        self.input_items: list[dict] = []
        self.input_data_custom = input_data_custom
        self.enable_cli_prints = enable_cli_prints

    # POLICY METHODS
    def should_append_tool_output(self) -> bool:
        return self.input_data_custom in {"tool", "tool_and_handoff"}

    def should_append_handoff_args(self) -> bool:
        return self.input_data_custom in {"handoff", "tool_and_handoff"}

    # SINGLE TURN (CORE)
    async def stream_turn(
        self, user_input: str
    ) -> AsyncGenerator[ReplEvent, None]:

        self.input_items.append(
            {"role": "user", "content": user_input}
        )

        # if self.enable_cli_prints:
        #     print(
        #         f"\n{bcolors.CYAN}{bcolors.BOLD}"
        #         f"User: {bcolors.ENDC}{user_input}"
        #     )

        start_time = time.time()

        result = Runner.run_streamed(
            starting_agent=self.agent,
            input=self.input_items,
            hooks=self.hooks,
        )

        async for event in self._handle_stream_events(result):
            yield event

        # Output finale
        # if self.enable_cli_prints:
        #     print(
        #         f"\n{bcolors.MIDNIGHT_BLUE}{bcolors.BOLD}"
        #         f"{self.agent.name}: {bcolors.ENDC}"
        #         f"{result.final_output}"
        #     )

        self.input_items.append(
            {"role": "assistant", "content": result.final_output}
        )

        elapsed = time.time() - start_time

        if self.enable_cli_prints:
            print(
                f"\n{bcolors.PURPLE}Elapsed time: "
                f"{elapsed:.4f} seconds{bcolors.ENDC}"
            )
            print(
                f"\n{bcolors.DARK_GRAY}LOG INPUT ITEMs:\n"
                f"{self.input_items}{bcolors.ENDC}"
            )

        yield ReplEvent(
            type="final",
            content=result.final_output or "",
        )

    # STREAM EVENT HANDLER
    async def _handle_stream_events(
        self, result: RunResultStreaming
    ) -> AsyncGenerator[ReplEvent, None]:

        async for event in result.stream_events():

            # TEXT STREAM
            if isinstance(event, RawResponsesStreamEvent):
                if isinstance(event.data, ResponseTextDeltaEvent):
                    if self.enable_cli_prints:
                        print(event.data.delta, end="", flush=True)

                    yield ReplEvent(
                        type="text_delta",
                        content=event.data.delta,
                    )

            # RUN ITEMS
            elif isinstance(event, RunItemStreamEvent):
                item = event.item

                if item.type == "tool_call_item":
                    msg = (
                        f"[tool call: `{item.raw_item.name}`"
                        f"({item.raw_item.arguments})]"
                    )

                    if self.enable_cli_prints:
                        print(
                            f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}"
                            f"{msg}{bcolors.ENDC}",
                            flush=True,
                        )

                    yield ReplEvent("tool_call", msg)

                elif item.type == "tool_call_output_item":
                    output = str(item.output)

                    if self.enable_cli_prints:
                        print(
                            f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}"
                            f"[tool output:\n {output}]"
                            f"{bcolors.ENDC}",
                            flush=True,
                        )

                    if self.should_append_tool_output():
                        self.input_items.append(
                            {"role": "assistant", "content": output}
                        )

                    yield ReplEvent("tool_output", output)

                elif item.type == "message_output_item":
                    message = ItemHelpers.text_message_output(item)

                    if self.enable_cli_prints:
                        print(message, end="", flush=True)

                    yield ReplEvent("message", message)

                elif item.type == "handoff_call_item":
                    msg = (
                        f"[Agent `{item.raw_item.name}` handed off "
                        f"with args: {item.raw_item.arguments}]"
                    )

                    if self.enable_cli_prints:
                        print(
                            f"\n{bcolors.BORDEAUX}{bcolors.BOLD}"
                            f"{msg}{bcolors.ENDC}"
                        )

                    if self.should_append_handoff_args():
                        self.input_items.append(
                            {
                                "role": "assistant",
                                "content": item.raw_item.arguments,
                            }
                        )

            # AGENT SWITCH
            elif isinstance(event, AgentUpdatedStreamEvent):
                if self.enable_cli_prints:
                    print(
                        f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}"
                        f"[Agent invoked: `{event.new_agent.name}`]"
                        f"{bcolors.ENDC}",
                        flush=True,
                    )

                yield ReplEvent(
                    type="agent_switch",
                    content=event.new_agent.name,
                )

    # ------ CLI LOOP ------
    async def run_demo_loop(self, *, ui: bool=False, user_q: str=None):
        """
        Run a simple REPL loop with the given agent.

        This utility allows quick manual testing and debugging of an agent from the
        command line. Conversation state is preserved across turns. Enter ``exit``
        or ``quit`` to stop the loop.

        Args:
            starting_agent: The starting agent to run.
            hooks: Optional run hooks for lifecycle management.
            stream: Whether to stream the agent output.
            input_data_custom: Mode for handling input data from tools and handoffs.
        """

        input_items = []

        if ui:
            user_input = user_q
            input_items.append({"role": "user", "content": user_input})

            # Stream token per token
            async for delta in self.stream_turn(user_input):
                yield delta  # Chainlit riceve i token in tempo reale

        else:
            # CLI loop infinito
            while True:
                try:
                    user_input = input(
                        f"\n{bcolors.CYAN}{bcolors.BOLD}User: {bcolors.ENDC}"
                    )
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if user_input.strip().lower() in EXIT_COMMANDS:
                    break

                if not user_input.strip():
                    continue

                input_items.append({"role": "user", "content": user_input})
                async for _ in self.stream_turn(user_input):
                    pass