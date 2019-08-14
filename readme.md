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
- Use a profile_name
  - `awsume <profile_name> -c` Will run awsume on `<profile_name>` as it normally would, but will open the console using the credentials from running awsume on `<profile_name>`.

### Get Console Link

- If you want to get the url itself instead of trying to open the console, use:

``` bash
awsume <profile_name> -cl
```

or

``` bash
awsume <profile_name> --console-link
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
