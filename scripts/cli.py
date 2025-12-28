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
from src.sql_agent.utils.repl import run_demo_loop
from src.logger import logger


def parse_args():
    """Parse command line arguments"""
    
    parser = argparse.ArgumentParser(
        description='Run an AI agent with customizable streaming and input modes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
                Examples:
                %(prog)s --input-mode tool_and_handoff
                %(prog)s --no-stream --input-mode tool
                """
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        default=True,
        help='Enable streaming mode (default: enabled)'
    )
    
    parser.add_argument(
        '--no-stream',
        action='store_false',
        dest='stream',
        help='Disable streaming mode'
    )
    
    parser.add_argument(
        '--input-mode',
        type=str,
        choices=['tool', 'handoff', 'tool_and_handoff', 'nothing_else'],
        default='nothing_else',
        help='Custom input data mode (default: nothing_else)'
    )
    
    return parser.parse_args()


async def main():
    """Main execution function"""
    args = parse_args()
    
    # Esegui l'agente
    logger.info(f"Starting agent: {agent.name}")
    logger.info(f"Stream: {args.stream}")
    logger.info(f"Input mode: {args.input_mode}\n")
    
    await run_demo_loop(
        starting_agent=agent,
        input_data_custom=args.input_mode,
        stream=args.stream
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
    
    except MaxTurnsExceeded:
        logger.error("Max turns (10) exceeded.")