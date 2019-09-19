import os
import logging
import click
from pilot.analysis import analyze_dataframe, mimetypes
from pilot.exc import AnalysisException

log = logging.getLogger(__name__)


@click.command(help='Analyze a dataframe and print the output', hidden=True)
@click.argument('dataframes',
                type=click.Path(exists=True, file_okay=True, dir_okay=True,
                                readable=True, resolve_path=True),
                nargs=-1)
def analyze(dataframes):
    """
    Run analytics on a dataframe and report the output without any other
    action. This is handy if the user isn't sure this will work, and may want
    to pass the --no-analyze flag to upload. Alternatively, they may simply
    want to better understand the contents of a dataframe.
    """
    for dataframe in dataframes:
        basename = os.path.basename(dataframe)
        if os.path.isdir(dataframe):
            click.secho('"{}" is a directory, skipping....'.format(basename))
            continue
        try:
            mimetype = mimetypes.detect_type(dataframe)
            click.secho('Analyzing {} ({})'.format(basename, mimetype))
            analysis = analyze_dataframe(dataframe, mimetype)
            if not analysis:
                click.secho('Unable to analyze {}'.format(basename))
                continue
            from pprint import pprint
            pprint(analysis)
        except AnalysisException as ae:
            click.secho('Error analyzing {}: {}'.format(basename, ae),
                        fg='yellow')
