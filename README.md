# s3proxy [![CircleCI](https://circleci.com/gh/uktrade/s3proxy.svg?style=svg)](https://circleci.com/gh/uktrade/s3proxy) [![Test Coverage](https://api.codeclimate.com/v1/badges/80938f6b27356411efd5/test_coverage)](https://codeclimate.com/github/uktrade/s3proxy/test_coverage)

> An OAuth-authenticated streaming proxy to S3


## Required environment variables

| Variable                 | Description                                                                                                           | Example                               |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `SSO_URL`                | The root URL to SSO                                                                                                   | `https://sso.domain.com/`             |
| `SSO_CLIENT_ID`          | The client ID of the SSO application                                                                                  | _not shown_                           |
| `SSO_CLIENT_SECRET`      | The client secret of the SSO application                                                                              | _not shown_                           |
| `AWS_DEFAULT_REGION`     | The AWS region of the S3 bucket                                                                                       | `eu-west-2`                           |
| `AWS_S3_BUCKET`          | The S3 bucket name, optionally including a key prefix (i.e. a "folder" in the bucket). No trailing slash is expected. | `my-bucket`<br>`my-bucket/key-prefix` |
| `AWS_S3_HEALTHCHECK_KEY` | The key of an object in the S3 bucket to be proxied without SSO authentication                                        | `healthcheck.txt`                     |

The below environment variables are also required, but typically populated by PaaS.

| Variable        | Description                                                      | Example                                                                       |
| --------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `PORT`          | The port for the application to listen on                        | `8080`                                                                        |
| `VCAP SERVICES` | A JSON-encoded dictionary containing the URI to a redis instance | `{"redis": [{"credentials": {"uri": "redis://my-redis.domain.com:6379/0"}}]}` |

## Optional environment variables

AWS authentication to access the buckets may be provided via keys made available as environment variables. If they are present, they will be used.

If this service is running on an AWS instance with a relevant IAM Role applied to the instance, these variables must be omitted in order to use the Role credentials

> Note that to use an IAM Instance Role no AWS credentials may be present in any of the standard locations on the instance, or they will be used in preference to the Role credentials.

| Variable                | Description                                                                        | Example     |
| ----------------------- | ---------------------------------------------------------------------------------- | ----------- |
| `AWS_ACCESS_KEY_ID`     | The AWS access key ID that has GetObject, and optionally ListBucket, permissions   | _not shown_ |
| `AWS_SECRET_ACCESS_KEY` | The secret part of the AWS access key                                              | _not shown_ |
| `KEY_PREFIX`            | A folder-like prefix to be prepended to all object keys. No slashes should be used | `my-folder` |

## Permissions and 404s

If the AWS user/role has the ListBucket permission, 404s are proxied through to the user to aid debugging.

## Shutdown

On SIGTERM any in-progress requests will complete before the process exits. At the time of writing PaaS will then forcibly kill the process with SIGKILL if it has not exited within 10 seconds.

## Range requests

The headers `range`, `content-range` and `accept-ranges` and proxied to allow range requests. This means that video should be able to be proxied with reasonable seeking behaviour.

## Parallel flows with new sessions

Parallel requests for users that have no existing cookies are supported

## Key-limitation

The path `/__redirect_from_sso` is used as part of SSO authentication. This corresponds to the key `__redirect_from_sso`, and so the object with this key cannot be proxied.

## Running locally

Ensure you have a docker daemon running and available.

* Copy the example env file cp .env.example .env
* Configure env vars (talk to SRE for values) - or use as-is, connecting to the local minio container instead of S3
* Build local docker instance:
  * `make build`
* Start the local docker instance:
  * `make up`
* Open a browser at http://localhost:8000/<object_key>

## Running tests

Ensure you have a docker daemon running and available, and that you have installed the `testing` dependencies via poetry.

Once you have the docker containers running locally (see above) simply `make test`
