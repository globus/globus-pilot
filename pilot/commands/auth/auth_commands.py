import os
import logging
import click

import pilot
from pilot.profile import profile
from pilot.config import config


log = logging.getLogger(__name__)


@click.command(help='Login with Globus')
@click.option('--refresh-tokens/--no-refresh-tokens', default=True,
              help='Request a refresh token to login indefinitely')
@click.option('--force/--no-force', default=False,
              help='Do a fresh login, ignoring any existing credentials')
@click.option('--local-server/--no-local-server', default=True,
              help='Start a local TCP server to handle the auth code')
@click.option('--browser/--no-browser', default=True,
              help='Automatically open the browser to login')
def login(refresh_tokens, force, local_server, browser):
    pc = pilot.commands.get_pilot_client()
    is_logged_in = pc.is_logged_in()
    if is_logged_in and not force:
        click.echo('You are already logged in.')
        return
    elif is_logged_in and force:
        pc.logout()

    prev_info = profile.load_user_info()
    pc.login(refresh_tokens=refresh_tokens,
             no_local_server=not local_server,
             no_browser=not browser,
             force=force)
    click.secho('You have been logged in.', fg='green')
    if prev_info != profile.load_user_info():
        m = ('Your personal info has been saved as: '
             f'\nName: \t{profile.name}'
             f'\nOrganization: \t{profile.organization}'
             '\n\nYou can update these with "pilot profile -i"')
        click.secho(m, fg='blue')


@click.command(help='Revoke local tokens')
@click.option('--purge', default=False, is_flag=True,
              help='Clear all transfer logs and user info')
def logout(purge):
    pc = pilot.commands.get_pilot_client()
    if pc.is_logged_in():
        pc.logout()
        click.secho('You have been logged out.', fg='green')
    else:
        click.echo('No user logged in, no tokens to clear.')
    if purge and os.path.exists(config.CFG_FILENAME):
        os.unlink(config.CFG_FILENAME)
        click.secho('All local user info and logs have been deleted.',
                    fg='green')


@click.command(help='Output Globus Identity used to login')
def whoami():
    info = config.get_user_info()
    if not info:
        click.echo('You are not logged in.')
        return
    click.echo(info['preferred_username'])
