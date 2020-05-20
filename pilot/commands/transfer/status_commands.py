import click

from pilot.commands import get_pilot_client
import globus_sdk

INACTIVE_STATES = ['SUCCEEDED', 'FAILED', 'CANCELED']


def update_tasks(transfer_tasks):
    """
    Update pending Globus Transfer tasks, and save the resulting status to
    the config. transfer tasks is a list of dicts as returned by
    config.get_pc.transfer_log()

    User must be logged in!
    """
    pc = get_pilot_client()
    auth = pc.get_authorizers()['transfer.api.globus.org']
    tc = globus_sdk.TransferClient(authorizer=auth)
    user_tasks = {r.data['task_id']: r.data for r in
                  tc.task_list(num_results=100).data}
    for task in transfer_tasks:
        task_data = user_tasks.get(task['task_id'])
        if not task_data:
            click.secho('Unable to update status for {}'.format(task['id']),
                        fg='yellow')
        else:
            status = task_data.get('nice_status') or task_data.get('status')
            pc.transfer_log.update_log(task['task_id'], status)


@click.command(help='Check status of transfers', name='status')
# @click.argument('task', required=False)
@click.option('-n', 'number', type=int, default=10,
              help='Number of tasks to list')
def status_command(number):
    pc = get_pilot_client()

    ordered_tlogs = []
    tlog_order = ['id', 'dataframe', 'status', 'start_time', 'task_id']
    # Fetch a limmited set of logs by the most recent entries
    tlogs = pc.transfer_log.get_log()[:number]

    pending_tasks = [t for t in tlogs if t['status'] not in INACTIVE_STATES]
    if pending_tasks:
        click.secho('Updating tasks...', fg='green')
        update_tasks(pending_tasks)
        tlogs = pc.transfer_log.get_log()[:number]

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
