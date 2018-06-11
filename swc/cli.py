import sys
import click
import requests
import pprint

from __version__ import __version__
from context import *
from nsrdb_cli import nsrdb
from nsrdb_cli import get_nsrdb_data
from sam_simulation_cli import sam




CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    version = __version__
    click.echo(f'SWC {version}. ❤ ')
    ctx.exit()

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
@click.pass_context
def main(ctx):
    click.echo('Welcome to SWC a wrapper of NSRDB and SAM 🔥!\n')
    click.secho('Starting the CLI\n', fg='blue')
    pass


main.add_command(nsrdb)
main.add_command(sam)

if __name__ == "__main__":
    main(obj={})
