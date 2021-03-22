# Awsume Console Plugin

_Awsume 4+ only_.

This is a plugin that enables you to use your assumed role credentials to open the AWS console in your default browser.

## Installation

```
pip install awsume-console-plugin
```

If you've installed awsume with `pipx`, this will install the console plugin in awsume's virtual environment:

```
pipx inject awsume awsume-console-plugin
```

## Usage

There are two ways to use this plugin.

- Use your current environment variables to open the console
  - `awsume -c` Will open the AWS console using the current environment variables
- Use the credentials returned from an awsume call
  - `awsume <profile_name> -c` Will run awsume on `<profile_name>` as it normally would, but will open the console using the credentials from running awsume on `<profile_name>`.
- Get a console link
  - `awsume <profile_name> -cl` Will run awsume on `<profile_name>` as it normally would, but will print a link to the console using the credentials from running awsume on `<profile_name>` and not attempt to open the default browser.
- Redirect to a service
  - `awsume <profile_name> -cs <service>` Will run awsume on `<profile_name>` as it normally would, but will open the console to a specific service page using the credentials from awsume.

### Get Console Link

- If you want to get the url itself instead of trying to open the console, use:

``` bash
awsume <profile_name> -cl
```

or

``` bash
awsume <profile_name> --console-link
```

### Service Page

- If you want to get a url that redirects you to a specific console's service page, use the `-cs flag`

``` bash
awsume <profile_name> -cs cloudformation
```

or

``` bash
awsume <profile_name> --console-service cloudformation
```

You can combine the console link and console service modifiers to print a link that redirects you to a specific service page:

``` bash
awsume <profile_name> -cls cloudformation
```

or

``` bash
awsume <profile_name> --console-link-service cloudformation
```

#### Notes

Some services have urls that are less-than-obvious. For instance, the step functions console url is `/states`, lightsail is `/ls`, etc. For this reason a default mapping is maintained to catch some of those common issues. Here's a list of what input maps to what url:

| input | url |
| --- | --- |
| cfn | cloudformation |
| ddb | dynamodb |
| ssm | systems-manager |
| stepfunctions | states |
| sfn | states |
| org | organizations |
| api | apigateway |
| cfnt | cloudfront |
| cw | cloudwatch |
| codecommit | codesuite/codecommit |
| codebuild | codesuite/codebuild |
| codedeploy | codesuite/codedeploy |
| codepipeline | codesuite/codepipeline |
| code | codesuite |
| r53 | route53 |
| route | route53 |
| lightsail | ls |
| eb | elasticbeanstalk |
| sar | serverlessrepo |
| sgw | storagegateway |
| wat | wellarchitected |
| sso | singlesignon |
| waf | wafv2 |

You can maintain your own custom mapping if you want, too. The `console.services` global configuration property is used to add additional service mappings.

```yaml
console:
  services:
    c: cloudformation
```

That config will add a mapping from input of `c` to a url of `cloudformation`.

#### Custom URLs

If you supply a url to the console service modifier, that url will be used as the redirect url. So if you want to view the cloudwatch logs for a lambda in a specific account, you can run:

```
awsume <profile> -cs https://console.{amazon_domain}/cloudwatch/home?region={region}#logEventViewer:group=/aws/lambda/<my_function>
```

## Custom Command

You can use awsume's configuration to store a custom command (in the `console.browser_command` key) that will be executed instead of the default `webbrowser.open()`. The command will be used with python's `str.format` call, so that you can supply where the url should go.

### Format arguments:

- `url` - the console url
- `profile` - the profile name

### Example

The following will open chrome using a unique profile so that you can open N-number of AWS consoles concurrently.

_Note you may need to adjust the path and other arguments on your machine._

```bash
$ awsume --config set console.browser_command "\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" --profile-directory=/tmp/{profile} \"{url}\""
```

The following will open chrome in incognito mode

```bash
$ awsume --config set console.browser_command "\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" -incognito \"{url}\""
```

The following will open firefox using a unique temporary profile:

```bash
$ awsume --config set console.browser_command "/Applications/Firefox.app/Contents/MacOS/firefox -profile /tmp/{profile} -no-remote \"{url}\""
```
