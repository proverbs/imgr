import os
import json
from shutil import copyfile

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


def _check_configuration():
    global _LOCAL_BASE
    if _LOCAL_BASE is None:
        raise ValueError('Please run `imgr config` first!')


@click.command()
@click.option('--local-base',
              type=click.Path(exists=True),
              required=True,
              help='Local dir for image hosting. Must be a git base dir.')
def configure(local_base):
    """Configure local base dir for image hosting."""
    base_dir = os.path.abspath(local_base)
    if not os.path.isdir(base_dir):
        raise ValueError('Please specify a dir!')
    with open(_CONFIGURE_PATH, 'w') as f:
        json.dump({'local-base': base_dir}, f)
        click.echo(f'Local base is set successfully to {base_dir}')


@click.command()
@click.argument('dir-name', type=str, required=True)
def mkdir(dir_name):
    """Create dir in the local base."""
    _check_configuration()
    new_dir = os.path.join(_LOCAL_BASE, dir_name)
    if os.path.exists(new_dir):
        raise ValueError(f'{new_dir} already exists!')
    os.makedirs(new_dir)
    click.echo(f'New dir created: {new_dir}')


@click.command()
@click.argument('src', type=click.Path(exists=True), required=True)
@click.argument('dst', type=str, required=True)
def add(src, dst):
    """Add an image to local base."""
    _check_configuration()
    dst_path = os.path.join(_LOCAL_BASE, dst)
    dst_dir = os.path.dirname(dst_path)
    if not os.path.exists(dst_dir):
        raise ValueError(f'{dst_dir} does not exist!')
    copyfile(src, dst_path)
    click.echo(f'Added new image: {dst_path}')


@click.group()
def cli():
    pass


cli.add_command(configure)
cli.add_command(mkdir)
cli.add_command(add)

if __name__ == '__main__':
    _init()
    cli()
