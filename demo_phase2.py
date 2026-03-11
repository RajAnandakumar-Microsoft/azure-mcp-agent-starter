"""Demonstration of Phase 2: Response Streaming (simulated)."""

import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

console = Console()


def demo_streaming():
    """Demonstrate streaming progress indicators."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Phase 2 Demo: Response Streaming[/bold cyan]\n"
            "[dim]Real-time progress indicators for tool calls[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Simulate a query
    query = "Show me all artifacts related to REQ-001"
    console.print(f"[bold cyan]Query:[/bold cyan] {query}")
    console.print()

    # Simulate processing with live updates
    with Live(console=console, refresh_per_second=10) as live_display:
        # Step 1: Initial processing
        status = Text.assemble(
            ("⏳ ", "cyan"),
            ("Processing your query...", "cyan"),
        )
        live_display.update(status)
        time.sleep(1.0)

        # Step 2: Calling tool
        status = Text.assemble(
            ("🔧 Calling tool: ", "yellow"),
            ("list_related_artifacts", "bold yellow"),
            ("...", "yellow"),
        )
        live_display.update(status)
        time.sleep(1.5)

        # Step 3: Tool completion with timing
        status = Text.assemble(
            ("✓ ", "green"),
            ("list_related_artifacts ", "bold green"),
            ("completed in 0.41s", "dim green"),
        )
        live_display.update(status)
        time.sleep(0.5)

        # Step 4: Submitting results
        status = Text.assemble(
            ("📤 ", "cyan"),
            ("Submitting tool results to agent...", "cyan"),
        )
        live_display.update(status)
        time.sleep(1.0)

        # Step 5: Agent thinking
        status = Text.assemble(
            ("🤔 ", "cyan"),
            ("Agent thinking...", "cyan"),
        )
        live_display.update(status)
        time.sleep(1.5)

    # Show final response
    console.print()
    response_text = """
## Related Artifacts for REQ-001

### 🔹 Requirement (JAMA)
- **Title:** User Authentication System
- **Status:** Approved
- **Priority:** High

### 🧩 Architecture Components (IcePanel)
1. **COMP-201** - Authentication Service
   - Fetched in parallel with COMP-204
2. **COMP-204** - API Gateway
   - Fetched in parallel with COMP-201

### 🔧 Azure DevOps Work Items
- **WI-1, WI-2, WI-7, WI-15** (4 work items)

---

**Performance:** Parallel execution achieved **3.9x speedup** over sequential fetching.
"""

    console.print(
        Panel(
            Markdown(response_text),
            title="[bold green]Agent Response[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()

    # Show key features
    console.print("[bold]✨ Phase 2 Features Demonstrated:[/bold]")
    console.print("  ✅ Real-time progress indicators (🔧 🤔 📤 ✓)")
    console.print("  ✅ Tool call visibility with timing")
    console.print("  ✅ Live status updates (no more spinner)")
    console.print("  ✅ Better UX with Rich Live display")
    console.print("  ✅ Combined with Phase 1 parallel execution")
    console.print()


if __name__ == "__main__":
    demo_streaming()
