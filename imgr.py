import os
import json
import subprocess
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
    # TODO: check if it's a git repo


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


def _git_status_clean():
    process = subprocess.Popen(['git', 'status', '--porcelain=v1'],
                               cwd=_LOCAL_BASE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if len(out) == 0:
        raise ValueError('Local base is clean, nothing new to push!')


def _git_add():
    process = subprocess.Popen(['git', 'add', '.'],
                               cwd=_LOCAL_BASE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        raise ValueError(err.decode('utf-8'))


def _git_commit(message):
    process = subprocess.Popen(['git', 'commit', '-m', message],
                               cwd=_LOCAL_BASE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        raise ValueError(err.decode('utf-8'))
    click.echo(out.decode('utf-8'))


def _git_push():
    process = subprocess.Popen(['git', 'push', '-u', 'origin', 'master'],
                               cwd=_LOCAL_BASE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        raise ValueError(err.decode('utf-8'))


@click.command()
@click.option('--message', type=str, required=True, help="Commit message.")
def push(message):
    """Commit and push to remote."""
    _check_configuration()
    _git_status_clean()
    _git_add()
    _git_commit(message)
    _git_push()
    click.echo('Pushed!')


@click.group()
def cli():
    pass


cli.add_command(configure)
cli.add_command(mkdir)
cli.add_command(add)
cli.add_command(push)

if __name__ == '__main__':
    _init()
    cli()
