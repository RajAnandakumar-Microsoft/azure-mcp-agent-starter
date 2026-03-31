"""
MCP Traceability Agent - Main Entry Point.

This script runs a local agent that demonstrates Azure AI Foundry capabilities
using the Microsoft Agent Framework.
"""

import json
import logging
import sys
import time

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
from rich.table import Table
import requests

from agent_app.config import AppConfig, load_config
from agent_app.tools import TOOL_FUNCTIONS, get_tool_definitions

# Configure logging - only show errors
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Suppress all Azure SDK logging
logging.getLogger("azure").setLevel(logging.ERROR)

# Create Rich console for beautiful output
console = Console()


def check_mcp_servers(config: AppConfig) -> dict[str, bool]:
    """Check health of all MCP servers.
    
    Args:
        config: Application configuration with MCP URLs.
        
    Returns:
        Dictionary mapping server names to health status (True=healthy, False=down).
    """
    import subprocess
    import os
    
    health_status = {}
    
    # Check unified demo server (serves both JAMA and IcePanel)
    demo_server_healthy = False
    if config.mcp.jama.transport == "http":
        try:
            response = requests.post(
                f"{config.mcp.jama.url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                headers={"Content-Type": "application/json"},
                timeout=2
            )
            demo_server_healthy = response.status_code == 200
        except Exception:
            demo_server_healthy = False
    
    # Both JAMA and IcePanel use the same unified server
    health_status["JAMA"] = demo_server_healthy
    health_status["IcePanel"] = demo_server_healthy
    
    # Check ADO (stdio) - verify node and script exist
    if config.mcp.ado.transport == "stdio":
        try:
            node_check = subprocess.run(["node", "--version"], capture_output=True, timeout=2)
            script_exists = os.path.exists(config.mcp.ado.args[0])
            health_status["ADO"] = node_check.returncode == 0 and script_exists
        except Exception:
            health_status["ADO"] = False
    
    return health_status


def display_mcp_status(health_status: dict[str, bool]) -> None:
    """Display MCP server health status in a panel.
    
    Args:
        health_status: Dictionary mapping server names to health status.
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Server", style="cyan")
    table.add_column("Status")
    
    for server, is_healthy in health_status.items():
        if is_healthy:
            status = "[green]✓ Connected[/green]"
        else:
            status = "[red]✗ Disconnected[/red]"
        table.add_row(server, status)
    
    console.print()
    console.print(Panel(
        table,
        title="[bold cyan]MCP Server Status[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))


def create_agent_client() -> AgentsClient:
    """
    Create and return an AgentsClient instance.

    Uses configuration from environment variables via load_config().

    Returns:
        AgentsClient configured for Azure AI Foundry Agent Service.
    """
    config = load_config()

    # Use Azure AD authentication (DefaultAzureCredential)
    credential = DefaultAzureCredential()

    client = AgentsClient(
        endpoint=config.azure.project_endpoint,
        credential=credential,
    )

    return client


def run_agent_with_tools_streaming(
    client: AgentsClient, config: AppConfig, user_prompt: str
) -> None:
    """
    Run the agent with tool support using streaming for real-time updates.

    Displays progress indicators as tools are called and streams the agent's
    response as tokens are generated.

    Args:
        client: The AgentsClient instance.
        config: Application configuration.
        user_prompt: The user's question or request.
    """
    try:
        # Get tool definitions
        tools = get_tool_definitions()

        # Create thread and run with tools
        with console.status("[cyan]Processing your query...", spinner="dots"):
            run = client.create_thread_and_run(
                agent_id=config.azure.agent_id,
                thread={"messages": [{"role": "user", "content": user_prompt}]},
                tools=tools,
            )

        # Track streaming state
        response_text = ""
        current_status = Text()

        # Poll and handle tool calls with streaming display
        with Live(
            console=console, refresh_per_second=10, transient=False
        ) as live_display:
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(0.5)
                run = client.runs.get(thread_id=run.thread_id, run_id=run.id)

                # Handle tool calls if the run requires action
                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Show which tool is being called with spinner
                        current_status = Text.assemble(
                            (f"🔧 Calling tool: ", "yellow"),
                            (f"{function_name}", "bold yellow"),
                            ("...", "yellow"),
                        )
                        live_display.update(current_status)

                        # Execute the tool function
                        if function_name in TOOL_FUNCTIONS:
                            start_time = time.time()
                            result = TOOL_FUNCTIONS[function_name](**function_args)
                            elapsed = time.time() - start_time

                            # Show tool completion with timing
                            current_status = Text.assemble(
                                ("✓ ", "green"),
                                (f"{function_name} ", "bold green"),
                                (f"completed in {elapsed:.2f}s", "dim green"),
                            )
                            live_display.update(current_status)
                            time.sleep(0.3)  # Brief pause to show completion

                            tool_outputs.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(result),
                                }
                            )

                    # Submit tool outputs and continue
                    if tool_outputs:
                        current_status = Text.assemble(
                            ("📤 ", "cyan"),
                            ("Submitting tool results to agent...", "cyan"),
                        )
                        live_display.update(current_status)

                        client.runs.submit_tool_outputs(
                            thread_id=run.thread_id,
                            run_id=run.id,
                            tool_outputs=tool_outputs,
                        )

                elif run.status == "in_progress":
                    # Show thinking indicator
                    current_status = Text.assemble(
                        ("🤔 ", "cyan"),
                        ("Agent thinking...", "cyan"),
                    )
                    live_display.update(current_status)

        # Display final response
        if run.status == "completed":
            # Get the messages from the thread
            messages = client.messages.list(thread_id=run.thread_id, order="asc")
            for msg in messages:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, "text"):
                            response_text = content.text.value
                            console.print()
                            console.print(
                                Panel(
                                    Markdown(response_text),
                                    title="[bold green]Agent Response[/bold green]",
                                    border_style="green",
                                    padding=(1, 2),
                                )
                            )
        else:
            console.print(f"[red]✗ Error: Run ended with status: {run.status}[/red]")
            if hasattr(run, "last_error") and run.last_error:
                console.print(f"[red]Details: {run.last_error}[/red]")

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]\n")


def run_agent_with_tools(
    client: AgentsClient, config: AppConfig, user_prompt: str
) -> None:
    """
    Run the agent with tool support (non-streaming fallback).

    Handles tool calls by executing local Python functions and submitting
    outputs back to the agent.

    Args:
        client: The AgentsClient instance.
        config: Application configuration.
        user_prompt: The user's question or request.
    """
    try:
        # Get tool definitions
        tools = get_tool_definitions()

        # Show spinner while creating thread and run
        with console.status("[cyan]Processing your query...", spinner="dots"):
            # Create thread and run with tools
            run = client.create_thread_and_run(
                agent_id=config.azure.agent_id,
                thread={"messages": [{"role": "user", "content": user_prompt}]},
                tools=tools,
            )

        # Poll and handle tool calls
        with console.status("[cyan]Agent thinking...", spinner="dots") as status:
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(0.5)
                run = client.runs.get(thread_id=run.thread_id, run_id=run.id)

                # Handle tool calls if the run requires action
                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Show which tool is being called
                        status.update(f"[yellow]Calling tool: {function_name}...")

                        # Execute the tool function
                        if function_name in TOOL_FUNCTIONS:
                            result = TOOL_FUNCTIONS[function_name](**function_args)
                            tool_outputs.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(result),
                                }
                            )

                    # Submit tool outputs and continue
                    if tool_outputs:
                        status.update("[cyan]Submitting tool results...")
                        client.runs.submit_tool_outputs(
                            thread_id=run.thread_id,
                            run_id=run.id,
                            tool_outputs=tool_outputs,
                        )

        if run.status == "completed":
            # Get the messages from the thread
            messages = client.messages.list(thread_id=run.thread_id, order="asc")
            for msg in messages:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, "text"):
                            # Display response in a panel with markdown formatting
                            response_text = content.text.value
                            console.print()
                            console.print(
                                Panel(
                                    Markdown(response_text),
                                    title="[bold green]Agent Response[/bold green]",
                                    border_style="green",
                                    padding=(1, 2),
                                )
                            )
        else:
            console.print(f"[red]✗ Error: Run ended with status: {run.status}[/red]")
            if hasattr(run, "last_error") and run.last_error:
                console.print(f"[red]Details: {run.last_error}[/red]")

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]\n")


def main_async() -> None:
    """
    Entry point for the agent application.

    Accepts user prompts in a loop until user types 'exit'.
    """
    config = load_config()
    client = create_agent_client()

    # Get the agent once at startup
    try:
        with console.status("[cyan]Connecting to Azure AI Foundry...", spinner="dots"):
            agent = client.get_agent(config.azure.agent_id)
    except Exception as e:
        console.print(
            f"\n[red]✗ Error: Cannot find agent '{config.azure.agent_id}' "
            "in your Foundry project.[/red]"
        )
        console.print("[yellow]Please verify the agent ID in your .env file.[/yellow]\n")
        sys.exit(1)

    # Display welcome header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]MCP Traceability Agent[/bold cyan]\n"
        "[dim]Connected to Azure AI Foundry[/dim]",
        border_style="cyan",
    ))
    
    # Check and display MCP server status
    with console.status("[cyan]Checking MCP server connections...", spinner="dots"):
        health_status = check_mcp_servers(config)
    display_mcp_status(health_status)
    
    console.print()
    console.print("[dim]Type your questions below. Type [bold]'exit'[/bold] or [bold]'quit'[/bold] to end the session.[/dim]")
    console.print()

    # Loop to accept multiple questions
    while True:
        try:
            # Show prompt with color
            user_input = console.input("[bold cyan]>[/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("\n[cyan]👋 Goodbye![/cyan]")
                break

            # Run the agent with tool support (streaming)
            run_agent_with_tools_streaming(client, config, user_input)
            console.print()  # Add blank line between responses

        except KeyboardInterrupt:
            console.print("\n\n[cyan]👋 Goodbye![/cyan]")
            break
        except EOFError:
            break


def main() -> None:
    """
    Main entry point for the agent application.
    """
    try:
        main_async()
    except KeyboardInterrupt:
        console.print("\n[cyan]👋 Interrupted. Goodbye![/cyan]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"[red]✗ Fatal error: {e}[/red]")
        sys.exit(1)
    finally:
        # Ensure all spawned MCP server subprocesses are cleaned up
        from agent_app.registry.server_registry import get_registry

        registry = get_registry()
        if registry is not None:
            registry.shutdown()


if __name__ == "__main__":
    main()
