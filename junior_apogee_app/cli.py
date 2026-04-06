import json

import click

from .audit import log_action
from .benchmark import BenchmarkSuite
from .persistence import save_result


@click.group()
def cli():
    """Junior Apogee App command-line interface."""
    pass


@cli.command()
@click.argument("report", required=False, default="metrics")
def report(report: str):
    """Generate a report (stub)."""
    click.echo(f"Generating {report} report (stub).")


@cli.command()
def list_agents():
    """Print the names of registered agent classes."""
    from .agents import list_agents as _list_agents

    names = _list_agents()
    if names:
        click.echo("Available agents:")
        for name in names:
            click.echo(f" - {name}")
    else:
        click.echo("(no agents registered)")


@cli.command()
@click.option("--task", type=str, default="{}", help="JSON-encoded task to run")
def run(task: str):
    """Execute a simple evaluation run against a dummy task."""
    from .orchestrator import Orchestrator

    try:
        task_obj = json.loads(task)
    except json.JSONDecodeError:
        click.echo("Invalid JSON for --task", err=True)
        return

    orchestrator = Orchestrator([])
    result = orchestrator.execute(task_obj)
    save_result(task_obj.get("id", ""), result)
    log_action("run", {"task": task_obj})
    click.echo(f"Result: {result}")


@cli.command()
def simulate():
    """Run the benchmarking simulation suite (stub)."""
    _suite = BenchmarkSuite()
    click.echo("Simulation mode: no tasks ingested yet")
