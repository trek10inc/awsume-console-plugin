import argparse
import json
import os
import sys
import subprocess
import shlex
import urllib
import webbrowser

import boto3
from awsume.awsumepy import hookimpl, safe_print

# Python 3 compatibility (python 3 has urlencode in parse sub-module)
URLENCODE = getattr(urllib, 'parse', urllib).urlencode
# Python 3 compatibility (python 3 has urlopen in parse sub-module)
URLOPEN = getattr(urllib, 'request', urllib).urlopen


@hookimpl
def add_arguments(parser: argparse.ArgumentParser):
    try:
        parser.add_argument('-c', '--console',
            action='store_true',
            default=False,
            dest='open_console',
            help='Open the AWS console to the AWSume\'d credentials',
        )
        parser.add_argument('-cl', '--console-link',
            action='store_true',
            default=False,
            dest='open_console_link',
            help='Show the link to open the console with the credentials',
        )
    except argparse.ArgumentError:
        pass


@hookimpl
def post_add_arguments(config: dict, arguments: argparse.Namespace, parser: argparse.ArgumentParser):
    if arguments.open_console_link:
        safe_print('Console link')
        arguments.open_console = True
    if arguments.open_console is True and arguments.profile_name is None and sys.stdin.isatty() and not arguments.json:
        safe_print('Console')
        session = boto3.session.Session()
        creds = session.get_credentials()
        url = get_console_url({
            'AccessKeyId': creds.access_key,
            'SecretAccessKey': creds.secret_key,
            'SessionToken': creds.token,
        })
        if arguments.open_console_link:
            safe_print(url)
        else:
            try:
                open_url(config, arguments, url)
            except Exception:
                safe_print('Cannot open browser: {}'.format(e))
                safe_print('Here is the link: {}'.format(url))
        exit(0)


@hookimpl
def post_get_credentials(config: dict, arguments: argparse.Namespace, profiles: dict, credentials: dict):
    if arguments.open_console:
        safe_print('Open console with awsumed creds!')
        url = get_console_url(credentials)
        if arguments.open_console_link:
            safe_print(url)
        else:
            try:
                open_url(config, arguments, url)
            except Exception as e:
                safe_print('Cannot open browser: {}'.format(e))
                safe_print('Here is the link: {}'.format(url))


def get_console_url(credentials: dict = None):
    credentials = credentials if credentials is not None else {}
    params = {
        'Action': 'getSigninToken',
        'Session': {
            'sessionId': credentials.get('AccessKeyId'),
            'sessionKey': credentials.get('SecretAccessKey'),
            'sessionToken': credentials.get('SessionToken'),
        },
    }
    request_url = 'https://signin.aws.amazon.com/federation?'
    response = URLOPEN(request_url + URLENCODE(params))
    raw = response.read()

    try:
        token = json.loads(raw)['SigninToken']
    except getattr(json.decoder, 'JSONDecoderError', ValueError):
        token = json.loads(raw.decode())['SigninToken']

    params = {
        'Action': 'login',
        'Issuer': '',
        'Destination': 'https://console.aws.amazon.com/console/home?region=' + credentials.get('Region', 'us-east-1'),
        'SigninToken': token
    }
    url = 'https://signin.aws.amazon.com/federation?'
    url += URLENCODE(params)
    return url


def open_url(config: dict, arguments: argparse.ArgumentParser, url: str):
    if config.get('console.browser_command'):
        safe_print('Using a custom browser command')
        browser_command = config.get('console.browser_command')
        command = browser_command.format(
            url=url,
            profile=arguments.target_profile_name,
        )
        subprocess.Popen(shlex.split(command), stdout=open(os.devnull, 'w'))
    else:
        webbrowser.open(url)
