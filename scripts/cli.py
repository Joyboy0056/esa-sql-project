# Usage: python -m scripts.cli --help
"""
AI Agent Runner - Execute agents with customizable streaming and input modes
"""
import argparse
import asyncio

from agents.exceptions import MaxTurnsExceeded
from agents import set_tracing_disabled
set_tracing_disabled(disabled=True)

from src.sql_agent.agent import collector as agent
from src.sql_agent.utils.repl import AgentRunner
from src.logger import logger


def parse_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="Run an AI agent with customizable input modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
               Examples:
                 python -m scripts.cli --input-mode tool_and_handoff
                 python -m scripts.cli --input-mode tool
               """
    )

    parser.add_argument(
        "--input-mode",
        type=str,
        choices=[
            "tool",
            "handoff",
            "tool_and_handoff",
            "nothing_else",
        ],
        default="nothing_else",
        help="Custom input data mode (default: nothing_else)",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    logger.info(f"Starting agent: {agent.name}")
    logger.info(f"Input mode: {args.input_mode}")

    runner = AgentRunner(
        starting_agent=agent,
        input_data_custom=args.input_mode,
        enable_cli_prints=True,
    )

    await runner.run_demo_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.error("Interrupted by user.")

    except MaxTurnsExceeded:
        logger.error("Max turns exceeded.")
