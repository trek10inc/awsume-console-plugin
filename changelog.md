# Awsume Console Plugin Changelog

## [1.1.2] - Alias Addition

- Adds `logs-insights` alias to CloudWatch logs insights

## [1.1.1] - Destination URL Templating

- Adds destination url templating
  - The only value currently templated into destination urls is `region`. So if the region us `us-east-1` and your url is `https://url.com/hello?region={region}`, the url will be templated into `https://url.com/hello?region=us-east-1`
- Adds `logs` mapping to direct you to the CloudWatch logs console
- Fixes handling of region name for using current credentials

## [1.1.0] - 2019-09-01 - Console Service Feature

- Adds support for opening the console to a specific service's console
  - `awsume profile -cs cloudformation` will open the cloudformation console
  - A mapping is maintained for some possible confusing services (like `stepfunctions` will be transformed to `states` by default)
  - A custom mapping can be maintained via the `console.services` configuration property
- Fixes custom browser command owning the process in some cases

## [1.0.2] - 2019-08-23 - Govcloud Support

- Adds support for govcloud regions

## [1.0.1] - 2019-08-18 - Bug Fix

- Fixed exception handling

## [1.0.0] - 2019-08-15 - Initial Release

- Initial release for the awsume console plugin
