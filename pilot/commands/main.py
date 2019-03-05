import click

from pilot.version import __version__
from pilot.commands.auth import auth_commands


@click.group()
def cli():
    pass


@click.command()
def version():
    click.echo(__version__)


cli.add_command(auth_commands.login)
cli.add_command(auth_commands.logout)
cli.add_command(auth_commands.whoami)
cli.add_command(version)
