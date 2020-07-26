import os
import json

import click

_CWD = os.getcwd()
_HOME = os.path.expanduser('~')
_CONFIGURE_PATH = os.path.join(_HOME, '.imgr.json')
_LOCAL_BASE = None


def _init():
    global _LOCAL_BASE
    if os.path.exists(_CONFIGURE_PATH):
        with open(_CONFIGURE_PATH, 'r') as f:
            _LOCAL_BASE = json.load(f)['local-base']
            click.echo(f'Using local base: {_LOCAL_BASE}')


@click.command()
@click.option('--local-base',
              type=click.Path(exists=True),
              required=True,
              help='Local dir for image hosting. Must be a git base dir.')
def configure(local_base):
    base_dir = os.path.abspath(local_base)
    if not os.path.isdir(base_dir):
        raise ValueError('Error: Please specify a dir!')
    with open(_CONFIGURE_PATH, 'w') as f:
        json.dump({'local-base': base_dir}, f)
        click.echo(f'Local base is set successfully to {base_dir}')


@click.group()
def cli():
    pass


cli.add_command(configure)

if __name__ == '__main__':
    _init()
    cli()
