import re
import os
import json
import http
import subprocess
from shutil import copyfile

import click
import requests

_CWD = os.getcwd()
_HOME = os.path.expanduser('~')
_CONFIGURE_PATH = os.path.join(_HOME, '.imgr.json')
_LOCAL_BASE = None
_RAW_BASE_URL = 'https://raw.githubusercontent.com/'
_RELATIVE_URL_REGEX = re.compile(r'git@github\.com:(.*?)\.git')


def _init():
    global _LOCAL_BASE
    if os.path.exists(_CONFIGURE_PATH):
        with open(_CONFIGURE_PATH, 'r') as f:
            _LOCAL_BASE = json.load(f)['local-base']
            click.echo(f'Using local base: {_LOCAL_BASE}')


def _check_configuration():
    global _LOCAL_BASE
    global _RAW_BASE_URL
    if _LOCAL_BASE is None:
        raise ValueError('Please run `imgr config` first!')
    _git_raw_base_url()


def _git_raw_base_url():
    global _RELATIVE_URL_REGEX
    global _RAW_BASE_URL
    process = subprocess.Popen(['git', 'remote', '-v'],
                               cwd=_LOCAL_BASE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        raise ValueError(err.decode('utf-8'))
    ext_url = None
    for line in out.decode('utf-8').split('\n'):
        match = _RELATIVE_URL_REGEX.search(line)
        if match:
            ext_url = match.group(1)
            break
    if not ext_url:
        raise ValueError('Git repo not configured correctly!')
    _RAW_BASE_URL += ext_url + '/master/'


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


def _check_remote_valide(url):
    try:
        hd = requests.head(url, timeout=1)
        return hd.status_code == http.HTTPStatus.OK
    except:
        return False


@click.command()
@click.argument('dst', type=str, default="", required=False)
def show(dst):
    """Show images' raw URLs."""
    _check_configuration()
    dst_path = os.path.join(_LOCAL_BASE, dst)
    if not os.path.exists(dst_path):
        raise ValueError(f'{dst_path} does not exist!')
    if os.path.isfile(dst_path):
        url = os.path.join(_RAW_BASE_URL, dst)
        remote_valid = _check_remote_valide(url)
        fg = 'red' if not remote_valid else None
        click.secho(f'{dst}\t {url}', fg=fg)
    else:
        for filename in os.listdir(dst_path):
            if os.path.isfile(os.path.join(dst_path, filename)):
                ext_url = os.path.join(dst, filename)
                url = os.path.join(_RAW_BASE_URL, ext_url)
                remote_valid = _check_remote_valide(url)
                fg = 'red' if not remote_valid else None
                click.secho(f'{ext_url}\t {url}', fg=fg)


@click.command()
@click.argument('dst', type=str, default="", required=False)
def ls(dst):
    """list all images and dirs."""
    _check_configuration()
    dst_path = os.path.join(_LOCAL_BASE, dst)
    if not os.path.exists(dst_path):
        raise ValueError(f'{dst_path} does not exist!')
    for filename in os.listdir(dst_path):
        if os.path.isfile(os.path.join(dst_path, filename)):
            relative_path = os.path.join(dst, filename)
            click.echo(f'\t{relative_path}', nl=False)
        elif not filename.startswith('.'):
            relative_path = os.path.join(dst, filename)
            click.secho(f'\t{relative_path}/', fg='red', nl=False)
    click.echo('')


@click.group()
def cli():
    pass


cli.add_command(configure)
cli.add_command(mkdir)
cli.add_command(add)
cli.add_command(push)
cli.add_command(show)
cli.add_command(ls)

if __name__ == '__main__':
    _init()
    cli()
