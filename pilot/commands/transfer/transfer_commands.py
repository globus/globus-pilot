import click


@click.command()
def upload():
    click.echo('upload command')


@click.command()
def download():
    click.echo('download command')
