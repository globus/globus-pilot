import click

from pilot.version import __version__
from pilot.commands.auth import auth_commands
from pilot.commands.search import search_commands, delete
from pilot.commands.transfer import transfer_commands, status_commands


@click.group()
def cli():
    pass


@click.command(help='Show version and exit')
def version():
    click.echo(__version__)


cli.add_command(auth_commands.login)
cli.add_command(auth_commands.logout)
cli.add_command(auth_commands.whoami)
cli.add_command(auth_commands.profile_command)

cli.add_command(search_commands.list_command)
cli.add_command(search_commands.describe)
cli.add_command(delete.delete_command)

cli.add_command(transfer_commands.upload)
cli.add_command(transfer_commands.download)
cli.add_command(status_commands.status)

cli.add_command(version)
