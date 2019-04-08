import logging
import click

from pilot.client import PilotClient
from pilot.config import config


log = logging.getLogger(__name__)


@click.command()
@click.option('--refresh-tokens/--no-refresh-tokens', default=True,
              help='Request a refresh token to login indefinitely')
@click.option('--force/--no-force', default=False,
              help='Do a fresh login, ignoring any existing credentials')
@click.option('--local-server/--no-local-server', default=True,
              help='Start a local TCP server to handle the auth code')
@click.option('--browser/--no-browser', default=True,
              help='Automatically open the browser to login')
def login(refresh_tokens, force, local_server, browser):
    pc = PilotClient()
    is_logged_in = pc.is_logged_in()
    if is_logged_in and not force:
        click.echo('You are already logged in.')
        return
    elif is_logged_in and force:
        pc.logout()

    pc.login(refresh_tokens=refresh_tokens,
             no_local_server=not local_server,
             no_browser=not browser,
             force=force)
    click.echo('You have been logged in.')


@click.command()
def logout():
    pc = PilotClient()
    if pc.is_logged_in():
        pc.logout()
        click.echo('You have been logged out.')
    else:
        click.echo('No user logged in, no logout necessary.')


@click.command()
def whoami():
    info = config.get_user_info()
    if not info:
        click.echo('You are not logged in.')
        return
    click.echo(info['preferred_username'])
