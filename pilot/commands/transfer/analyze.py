import logging
import click
import pilot
import traceback
from pilot.analysis import analyze_dataframe, mimetypes
from pilot.exc import AnalysisException

log = logging.getLogger(__name__)

@click.command(help='Analyze a dataframe and print the output')
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                readable=True, resolve_path=True),)
def analyze(dataframe):
    """
    Run analytics on a dataframe and report the output without any other
    action. This is handy if the user isn't sure this will work, and may want
    to pass the --no-analyze flag to upload. Alternatively, they may simply
    want to better understand the contents of a dataframe.
    """
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    try:
        mimetype = mimetypes.detect_type(dataframe)
        log.debug(mimetype)
        click.secho('Analyzing {}'.format(dataframe))
        analysis = analyze_dataframe(dataframe, mimetype)
        from pprint import pprint
        pprint(analysis)
    except AnalysisException as ae:
        click.secho('Error analyzing {}, skipping...'.format(dataframe),
                    fg='yellow')
        traceback.print_exception(*ae.original_exc_info)
