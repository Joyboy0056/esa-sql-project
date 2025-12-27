from __future__ import annotations

from typing import Any, Literal, Set

from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent

from agents.agent import Agent
from agents.items import ItemHelpers, TResponseInputItem, HandoffCallItem
from agents.result import RunResultBase
from agents.run import Runner
from agents.stream_events import AgentUpdatedStreamEvent, RawResponsesStreamEvent, RunItemStreamEvent
from agents.lifecycle import RunHooks

import time

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


# Tipo più specifico per le opzioni di input personalizzato
InputDataMode = Literal["tool", "handoff", "tool_and_handoff", "nothing_else"]

# Set di comandi di uscita per performance migliori
EXIT_COMMANDS: Set[str] = {"exit", "quit", "stop", "cl"}


def should_append_tool_output(mode: InputDataMode) -> bool:
    """Determina se aggiungere l'output del tool agli input_items."""
    return mode in {"tool", "tool_and_handoff"}


def should_append_handoff_args(mode: InputDataMode) -> bool:
    """Determina se aggiungere gli argomenti di handoff agli input_items."""
    return mode in {"handoff", "tool_and_handoff"}


async def handle_stream_events(
    result: RunResultBase, 
    input_items: list, 
    mode: InputDataMode
) -> None:
    """Gestisce gli eventi di streaming in modo unificato."""
    async for event in result.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                
        elif isinstance(event, RunItemStreamEvent):
            if event.item.type == "tool_call_item":
                print(f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}[tool call: `{event.item.raw_item.name}`({event.item.raw_item.arguments})]{bcolors.ENDC}", flush=True)
                
            elif event.item.type == "tool_call_output_item":
                print(f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}[tool output:\n {str(event.item.output)}]{bcolors.ENDC}", flush=True)
                if should_append_tool_output(mode):
                    input_items.append({"role": "assistant", "content": event.item.output})
                    
            elif event.item.type == "message_output_item":
                message = ItemHelpers.text_message_output(event.item)
                print(message, end="", flush=True)
                
            elif event.item.type == "handoff_call_item":
                print(f"\n{bcolors.BORDEAUX}{bcolors.BOLD}[Agent `{event.item.raw_item.name}` handed off with args: {event.item.raw_item.arguments}]{bcolors.ENDC}")
                if should_append_handoff_args(mode):
                    input_items.append({"role": "assistant", "content": event.item.raw_item.arguments})
                    
        elif isinstance(event, AgentUpdatedStreamEvent):
            print(f"\n{bcolors.DARK_GRAY}{bcolors.BOLD}[Agent invoked: `{event.new_agent.name}`]{bcolors.ENDC}", flush=True)


async def run_demo_loop(
    starting_agent: Agent[Any], 
    hooks: RunHooks = None, 
    *, 
    stream: bool = True, 
    input_data_custom: InputDataMode = "nothing_else"
) -> None:
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
    current_agent = starting_agent
    input_items = []
    
    while True:
        try:
            user_input = input(f"\n{bcolors.CYAN}{bcolors.BOLD}User: {bcolors.ENDC}")
        except (EOFError, KeyboardInterrupt):
            print()
            break
            
        # Controllo più efficiente per i comandi di uscita
        if user_input.strip().lower() in EXIT_COMMANDS:
            break
            
        if not user_input.strip():
            continue

        input_items.append({"role": "user", "content": user_input})

        if stream:
            start_time = time.time()
            
            result = Runner.run_streamed(
                starting_agent=current_agent, 
                input=input_items,
                hooks=hooks
            )
            
            # Gestione unificata degli eventi di streaming
            await handle_stream_events(result, input_items, input_data_custom)
            
            print()  # Newline dopo gli eventi
            
            # Display dell'output dell'agente
            print(f"\n{bcolors.MIDNIGHT_BLUE}{bcolors.BOLD}{current_agent.name}: {bcolors.ENDC}{result.final_output}")
            
            # Timing info
            elapsed_time = time.time() - start_time
            print(f"\n{bcolors.PURPLE}Elapsed time: {elapsed_time:.4f} seconds{bcolors.ENDC}")
            
            # Debug info
            print(f"\n{bcolors.DARK_GRAY}TEST INPUT ITEM: \n{input_items}{bcolors.ENDC}")
            
        else:
            # Modalità non-streaming
            result = await Runner.run(
                starting_agent=current_agent, 
                input=input_items,
                hooks=hooks
            )
            
            if result.final_output is not None:
                print(f"\n{bcolors.MIDNIGHT_BLUE}{bcolors.BOLD}{current_agent.name}: {bcolors.ENDC}{result.final_output}")
        
        # Aggiunta della risposta dell'assistente agli input_items
        input_items.append({"role": "assistant", "content": result.final_output})