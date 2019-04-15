import click

from pilot.config import config
from pilot.client import PilotClient
import globus_sdk

PENDING_TASK_STATES = ['Accepted', 'ACTIVE', 'INACTIVE']


def update_tasks(transfer_tasks):
    """
    Update pending Globus Transfer tasks, and save the resulting status to
    the config. transfer tasks is a list of dicts as returned by
    config.get_transfer_log()

    User must be logged in!
    """
    pc = PilotClient()
    auth = pc.get_authorizers()['transfer.api.globus.org']
    tc = globus_sdk.TransferClient(authorizer=auth)
    statuses = {r.data['task_id']: r.data['status'] for r in
                tc.task_list(num_results=100).data}
    for task in transfer_tasks:
        status = statuses.get(task['task_id'])
        if not status:
            click.secho('Unable to update status for {}'.format(task['id']),
                        fg='yellow')
        else:
            config.update_transfer_log(task['task_id'], status)


@click.command(help='Check status of transfers')
# @click.argument('task', required=False)
@click.option('-n', 'number', type=int, default=10,
              help='Number of tasks to list')
def status(number):

    ordered_tlogs = []
    tlog_order = ['id', 'dataframe', 'status', 'start_time', 'task_id']
    # Fetch a limmited set of logs by the most recent entries
    tlogs = config.get_transfer_log()[:number]

    pending_tasks = [t for t in tlogs if t['status'] in PENDING_TASK_STATES]
    if pending_tasks:
        click.secho('Updating tasks...', fg='green')
        update_tasks(pending_tasks)
        tlogs = config.get_transfer_log()

    for tlog in tlogs:
        tlog['id'] = str(tlog['id'])
        tlog['start_time'] = tlog['start_time'].strftime('%Y-%m-%d %H:%M')
        ordered_tlogs.append([tlog[item] for item in tlog_order])

    fmt = '{:4.3}{:30.29}{:10.11}{:18.17}{:37.36}'
    header_names = ['ID', 'Dataframe', 'Status', 'Start Time', 'Task ID']
    headers = fmt.format(*header_names)
    output = '\n'.join([fmt.format(*items) for items in ordered_tlogs])

    click.echo(headers)
    click.echo(output)
