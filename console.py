import argparse
import json
import os
import sys
import subprocess
import urllib
import webbrowser
from urllib.parse import urlparse

import boto3
from awsume.awsumepy import hookimpl, safe_print
from awsume.awsumepy.lib.logger import logger

# Python 3 compatibility (python 3 has urlencode in parse sub-module)
URLENCODE = getattr(urllib, 'parse', urllib).urlencode
# Python 3 compatibility (python 3 has urlopen in parse sub-module)
URLOPEN = getattr(urllib, 'request', urllib).urlopen

SERVICE_MAPPING = {
    'cfn': 'cloudformation',
    'ddb': 'dynamodb',
    'ssm': 'systems-manager',
    'stepfunctions': 'states',
    'sfn': 'states',
    'org': 'organizations',
    'api': 'apigateway',
    'api': 'apigateway',
    'cfnt': 'cloudfront',
    'cw': 'cloudwatch',
    'codecommit': 'codesuite/codecommit',
    'codebuild': 'codesuite/codebuild',
    'codedeploy': 'codesuite/codedeploy',
    'codepipeline': 'codesuite/codepipeline',
    'code': 'codesuite',
    'r53': 'route53',
    'route': 'route53',
    'lightsail': 'ls',
    'eb': 'elasticbeanstalk',
    'sar': 'serverlessrepo',
    'sgw': 'storagegateway',
    'wat': 'wellarchitected',
    'sso': 'singlesignon',
    'waf': 'wafv2',
}


@hookimpl
def add_arguments(parser: argparse.ArgumentParser):
    try:
        parser.add_argument('-c', '--console',
            action='store_true',
            default=False,
            dest='console',
            help='Open AWS console',
        )
        parser.add_argument('-cl', '--console-link',
            action='store_true',
            default=False,
            dest='console_link',
            help='Get a sign-on url',
        )
        parser.add_argument('-cs', '--console-service',
            action='store',
            default=False,
            dest='console_service',
            metavar='service',
            help='Open the console to a specific service',
        )
        parser.add_argument('-cls', '-csl', '--console-service-link', '--console-link-service',
            action='store',
            default=False,
            dest='console_link_service',
            metavar='service',
            help='Get a sign-on url to a specific service',
        )
    except argparse.ArgumentError:
        pass


@hookimpl
def post_add_arguments(config: dict, arguments: argparse.Namespace, parser: argparse.ArgumentParser):
    get_url, open_browser, print_url, service = parse_args(arguments, config)

    if get_url is True and arguments.profile_name is None and sys.stdin.isatty() and not arguments.json:
        logger.debug('Openning console with current credentials')
        session = boto3.session.Session()
        creds = session.get_credentials()
        url = get_console_url({
            'AccessKeyId': creds.access_key,
            'SecretAccessKey': creds.secret_key,
            'SessionToken': creds.token,
        }, service)

        if print_url:
            safe_print(url)
        elif open_browser:
            try:
                open_url(config, arguments, url)
            except Exception as e:
                safe_print('Cannot open browser: {}'.format(e))
                safe_print('Here is the link: {}'.format(url))
        exit(0)


@hookimpl
def post_get_credentials(config: dict, arguments: argparse.Namespace, profiles: dict, credentials: dict):
    get_url, open_browser, print_url, service = parse_args(arguments, config)

    if get_url:
        logger.debug('Openning console with awsume\'d credentials')
        url = get_console_url(credentials, service)
        logger.debug('URL: {}'.format(url))

        if print_url:
            safe_print(url)
        elif open_browser:
            try:
                open_url(config, arguments, url)
            except Exception as e:
                safe_print('Cannot open browser: {}'.format(e))
                safe_print('Here is the link: {}'.format(url))


def parse_args(arguments: argparse.Namespace, config: dict) -> tuple:
    get_url = False
    open_browser = False
    print_url = False
    service = 'console'

    if arguments.console:
        get_url = True
        open_browser = True
    if arguments.console_link:
        get_url = True
        print_url = True
    if arguments.console_service:
        get_url = True
        open_browser = True
        service = get_service(arguments.console_service, config)
    if arguments.console_link_service:
        get_url = True
        print_url = True
        service = get_service(arguments.console_link_service, config)

    return get_url, open_browser, print_url, service


def get_service(requested_service: str, config: dict) -> str:
    config_services = config.get('console', {}).get('services', {})
    service_mapping = { **SERVICE_MAPPING, **config_services }
    return service_mapping.get(requested_service, requested_service)


def is_url(string: str) -> bool:
    return urlparse(string).scheme != ''


def get_console_url(credentials: dict = None, destination: str = None):
    amazon_domain = 'amazonaws-us-gov' if 'gov' in str(credentials.get('Region')) else 'aws.amazon'
    logger.debug('Amazon domain: %s', amazon_domain)
    credentials = credentials if credentials is not None else {}
    logger.debug('Credentials: {}'.format(json.dumps(credentials, default=str, indent=2)))
    params = {
        'Action': 'getSigninToken',
        'Session': {
            'sessionId': credentials.get('AccessKeyId'),
            'sessionKey': credentials.get('SecretAccessKey'),
            'sessionToken': credentials.get('SessionToken'),
        },
    }
    logger.debug('Get console url request params: {}'.format(json.dumps(params, default=str, indent=2)))
    request_url = 'https://signin.' + amazon_domain + '.com/federation?'
    response = URLOPEN(request_url + URLENCODE(params))
    raw = response.read()

    try:
        token = json.loads(raw)['SigninToken']
    except getattr(json.decoder, 'JSONDecoderError', ValueError):
        token = json.loads(raw.decode())['SigninToken']
    logger.debug('Signin token: {}'.format(token))
    region = credentials.get('Region') or 'us-east-1'
    logger.debug('Region: {}'.format(region))
    params = {
        'Action': 'login',
        'Issuer': '',
        'Destination': destination if is_url(destination) else 'https://console.' + amazon_domain + '.com/' + destination + '/home?region=' + region,
        'SigninToken': token
    }
    logger.debug('URL params: {}'.format(json.dumps(params, default=str, indent=2)))
    url = 'https://signin.' + amazon_domain + '.com/federation?'
    url += URLENCODE(params)
    return url


def open_url(config: dict, arguments: argparse.ArgumentParser, url: str):
    if config.get('console', {}).get('browser_command'):
        logger.debug('Using custom browser command')
        browser_command = config['console']['browser_command']
        logger.debug('browser_command: {}'.format(browser_command))
        command = browser_command.format(
            url=url,
            profile=arguments.target_profile_name,
        )
        logger.debug('Command: {}'.format(command))
        with open(os.devnull, 'w') as f:
            subprocess.Popen(command, stdout=f, stderr=f, shell=True, preexec_fn=os.setpgrp)
    else:
        webbrowser.open(url)
