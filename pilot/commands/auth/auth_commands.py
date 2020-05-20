import os
import re
import logging
import globus_sdk
import click

import pilot
import pilot.exc
from pilot.commands import input_validation, endpoint_utils


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
    scopes = pc.context.get_value('scopes') or pc.DEFAULT_SCOPES
    pc.login(refresh_tokens=refresh_tokens,
             no_local_server=not local_server,
             no_browser=not browser,
             force=force,
             requested_scopes=scopes)
    if not pc.project.load_all():
        log.debug('NO project info saved, updating...')
        pc.context.update_with_diff()
    click.secho('You have been logged in.', fg='green')

    local_ep = (pc.profile.load_option('local_endpoint') or
                globus_sdk.LocalGlobusConnectPersonal().endpoint_id)
    local_path = pc.profile.load_option('local_endpoint_path')
    log.debug('Local Endpoint set to {}:{}'.format(local_ep, local_path))
    tc = pc.get_transfer_client()
    try:
        if local_ep:
            name = tc.get_endpoint(local_ep).data['display_name']
            pc.profile.save_option('local_endpoint', local_ep)
            pc.profile.save_option('local_endpoint_path', local_path)
            pc.profile.save_option('local_endpoint_name', name)
            endpoint_utils.test_local_endpoint()
    except pilot.exc.LocalEndpointUnresponsive as leu:
        log.debug('Endpoint UUID: {}, local path: {}'
                  .format(local_ep, local_path))
        click.secho(str(leu), fg='yellow')
    if prev_info != pc.profile.load_user_info():
        pitems = [('Name:', pc.profile.name),
                  ('Organization:', pc.profile.organization),
                  ('Local Endpoint:', pc.profile.load_option(
                      'local_endpoint_name'))]
        pstr = '\n'.join(['{:16}{}'.format(t, v) for t, v in pitems])
        report = (
            'Your personal info has been saved as: \n{}\n\n'
            'You can update these with "pilot profile -i"'.format(pstr)
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
    if purge and os.path.exists(pc.config_file):
        os.unlink(pc.config_file)
        click.secho('All local user info and logs have been deleted.',
                    fg='green')


@click.command(name='profile', help='Output Globus Identity used to login')
@click.option('-i', '--interactive', default=False, is_flag=True,
              help='Interactively set all profile options')
@click.option('--local-endpoint', help='Set local endpoint (ep:/my/path)')
def profile_command(interactive, local_endpoint):
    pc = pilot.commands.get_pilot_client()
    profile_queries = {
        'name': {
            'prompt': 'Name', 'default': pc.profile.name,
            'help': 'When you upload files, your name will be used as the '
                    'author',
            'validation': [],
        },
        'organization': {
            'prompt': 'Organization', 'default': pc.profile.organization,
            'help': 'When you upload files, your organization will be listed',
            'validation': [],
        },
    }
    if local_endpoint:
        pattern = r'(?P<endpoint>[\w-]{36})(:(?P<path>[\w/~]+))?'
        match = re.match(pattern, local_endpoint)
        if not match:
            click.secho('Provide your local endpoint in the notation: '
                        'myendpoint:/my/path', fg='red')
            return
        tc = pc.get_transfer_client()
        matchd = match.groupdict()
        try:
            tc.operation_ls(matchd['endpoint'], path=matchd.get('path'))
            name = tc.get_endpoint(matchd['endpoint']).data['display_name']
            pc.profile.save_option('local_endpoint', matchd['endpoint'])
            pc.profile.save_option('local_endpoint_path', matchd['path'])
            pc.profile.save_option('local_endpoint_name', name)
            click.secho('Your local endpoint has been set!', fg='green')
        except globus_sdk.exc.TransferAPIError as tapie:
            click.secho('Unable to access endpoint, please choose a path where'
                        ' you have read/write access: {}'
                        ''.format(tapie.message), fg='red')

    if interactive:
        od = ['name', 'organization']
        iv = input_validation.InputValidator(queries=profile_queries, order=od)
        info = pc.profile.load_user_info()
        new_profile = iv.ask_all()
        info.update(new_profile)
        pc.profile.save_user_info(info)
        click.secho('Your information has been updated', fg='green')
        return
    info = pc.profile.load_user_info()
    pitems = [('Name:', pc.profile.name),
              ('Organization:', pc.profile.organization),
              ('Identity: ', pc.profile.load_option('preferred_username')),
              ('Local Endpoint:', info.get('local_endpoint_name')),
              ('Local Path:', info.get('local_endpoint_path')),
              ('Endpoint UUID:', info.get('local_endpoint')),
              ('Config File:', pc.config_file),
              ]
    pstr = '\n'.join(['{:16}{}'.format(t, v) for t, v in pitems])
    click.echo('Your Profile: \n{}\n'.format(pstr))
