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
from awsume.awsumepy.lib import exceptions

# Python 3 compatibility (python 3 has urlencode in parse sub-module)
URLENCODE = getattr(urllib, 'parse', urllib).urlencode
# Python 3 compatibility (python 3 has urlopen in parse sub-module)
URLOPEN = getattr(urllib, 'request', urllib).urlopen

SERVICE_MAPPING = {
    'api': 'apigateway',
    'appconfig': 'systems-manager/appconfig',
    'appstream': 'appstream2',
    'budgets': 'billing/home?#/budgets',
    'c9': 'cloud9',
    'ce': 'cost-management',
    'cfn': 'cloudformation',
    'cfnt': 'cloudfront',
    'chime': 'https://chime.aws.amazon.com',
    'code': 'codesuite',
    'codebuild': 'codesuite/codebuild',
    'codecommit': 'codesuite/codecommit',
    'codedeploy': 'codesuite/codedeploy',
    'codepipeline': 'codesuite/codepipeline',
    'codestar': 'codesuite/codestar',
    'codeartifact': 'codesuite/codeartifact',
    'cw': 'cloudwatch',
    'ddb': 'dynamodb',
    'dms': 'dms/v2',
    'documentdb': 'docdb',
    'eb': 'elasticbeanstalk',
    'ec': 'elasticache',
    'es': 'elasticsearch',
    'event': 'events',
    'eventbridge': 'events',
    'gd': 'guardduty',
    'honey': 'honeycode',
    'k8s': 'eks',
    'l': 'lambda',
    'lightsail': 'ls',
    'logs-insights': 'https://{region}.console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:logs-insights',
    'logs': 'https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups',
    'mq': 'amazon-mq',
    'org': 'organizations',
    'orgs': 'organizations',
    'qs': 'https://quicksight.aws.amazon.com',
    'r53': 'route53',
    'route': 'route53',
    'sar': 'serverlessrepo',
    'secret': 'secretsmanager',
    'sfn': 'states',
    'sgw': 'storagegateway',
    'snow': 'importexport',
    'ssm': 'systems-manager',
    'sso': 'singlesignon',
    'stepfunctions': 'states',
    'sumerian': 'sumerianv2',
    'waf': 'wafv2',
    'wat': 'wellarchitected',
    'workdocs': 'zocalo',
    'workmail': 'workmail/v2',
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
        parser.add_argument('-cls', '-csl',
            action='store',
            default=False,
            dest='console_link_service',
            metavar='service',
            help='Get a sign-on url to a specific service',
        )
        parser.add_argument('-w', '--without-authentication',
            action='store_true',
            default=False,
            dest='console_without_authentication',
            help='Open AWS console directly without authentication',
        )
    except argparse.ArgumentError:
        pass


@hookimpl
def post_add_arguments(config: dict, arguments: argparse.Namespace, parser: argparse.ArgumentParser):
    get_url, open_browser, print_url, service = parse_args(arguments, config)

    if get_url is True and arguments.profile_name is None and arguments.role_arn is None and sys.stdin.isatty() and not arguments.json:
        logger.debug('Opening console with current credentials')
        session = boto3.session.Session()
        creds = session.get_credentials()
        if not creds:
            raise exceptions.NoCredentialsError('No credentials to open the console with')
        region = arguments.region or session.region_name or config.get('region')
        url = get_console_url({
            'AccessKeyId': creds.access_key,
            'SecretAccessKey': creds.secret_key,
            'SessionToken': creds.token,
            'Region': region,
        }, service, arguments.console_without_authentication)

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
        logger.debug('Opening console with awsume\'d credentials')
        url = get_console_url(credentials, service, arguments.console_without_authentication)
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


def template_url(url: str, **kwargs) -> str:
    logger.debug('Templating url with: %s', json.dumps(kwargs, indent=2, default=str))
    for key, value in kwargs.items():
        url = url.replace('{%s}' % key, value)
    logger.debug('Destination url: %s', url)
    return url


def get_console_url(credentials: dict = None, destination: str = None, without_authentication: bool = False):
    region = credentials.get('Region') or 'us-east-1'
    logger.debug('Region: {}'.format(region))
    if region.startswith('us-gov-'):
        amazon_domain = 'amazonaws-us-gov.com'
    elif region.startswith('cn-'):
        amazon_domain = 'amazonaws.cn'
    else:
        amazon_domain = 'aws.amazon.com'

    target_url = template_url(destination, region=region, amazon_domain=amazon_domain) if is_url(destination) else 'https://console.' + amazon_domain + '/' + destination + '/home?region=' + region

    if without_authentication:
        return target_url

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
    request_url = 'https://signin.' + amazon_domain + '/federation?'
    response = URLOPEN(request_url + URLENCODE(params))
    raw = response.read()

    try:
        token = json.loads(raw)['SigninToken']
    except getattr(json.decoder, 'JSONDecoderError', ValueError):
        token = json.loads(raw.decode())['SigninToken']
    logger.debug('Signin token: {}'.format(token))
    params = {
        'Action': 'login',
        'Issuer': '',
        'Destination': target_url,
        'SigninToken': token,
    }
    logger.debug('URL params: {}'.format(json.dumps(params, default=str, indent=2)))
    url = 'https://signin.' + amazon_domain + '/federation?'
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
