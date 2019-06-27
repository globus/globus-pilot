import os
import logging
import click

import pilot


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

    prev_info = pc.profile.load_user_info()
    pc.login(refresh_tokens=refresh_tokens,
             no_local_server=not local_server,
             no_browser=not browser,
             force=force)
    if not pc.project.load_all():
        log.debug('NO project info saved, updating...')
        pc.project.update_with_diff()
    click.secho('You have been logged in.', fg='green')
    if prev_info != pc.profile.load_user_info():
        report = (
            'Your personal info has been saved as:\n{:15}{}\n{:15}{}\n'
            '\n\nYou can update these with "pilot profile -i"'.format(
                'Name:', pc.profile.name, 'Organization:',
                pc.profile.organization
            )
        )
        click.secho(report, fg='blue')


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
    if purge and os.path.exists(pc.config.CFG_FILENAME):
        os.unlink(pc.config.CFG_FILENAME)
        click.secho('All local user info and logs have been deleted.',
                    fg='green')


@click.command(help='Output Globus Identity used to login')
def whoami():
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
    else:
        click.echo(pc.profile.load_user_info())


@click.command(name='profile', help='Output Globus Identity used to login')
@click.option('-i', '--interactive', default=False, is_flag=True,
              help='Interactively set all profile options')
def profile_command(interactive):
    pc = pilot.commands.get_pilot_client()
    if interactive:
        pc.profile.name = (
            input(f'Name ({pc.profile.name})> ') or pc.profile.name
        )
        pc.profile.organization = (
            input(f'Organization ({pc.profile.organization})> ') or
            pc.profile.organization
        )
        click.secho('Your information has been updated', fg='green')
        return
    report = 'Your profile:\n{:15}{}\n{:15}{}\n'.format(
        'Name:', pc.profile.name, 'Organization:', pc.profile.organization
    )
    click.echo(report)
