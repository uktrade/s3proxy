# s3proxy [![CircleCI](https://circleci.com/gh/uktrade/s3proxy.svg?style=svg)](https://circleci.com/gh/uktrade/s3proxy) [![Test Coverage](https://api.codeclimate.com/v1/badges/80938f6b27356411efd5/test_coverage)](https://codeclimate.com/github/uktrade/s3proxy/test_coverage)

> An OAuth-authenticated streaming proxy to S3


## Environment variables

### Required

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

### Optional

AWS authentication to access the buckets may be provided via keys made available as environment variables. If they are present, they will be used.

If this service is running on an AWS instance with a relevant IAM Role applied to the instance, these variables must be omitted in order to use the Role credentials

> Note that to use an IAM Instance Role no AWS credentials may be present in any of the standard locations on the instance, or they will be used in preference to the Role credentials.

| Variable                | Description                                                                        | Example     |
| ----------------------- | ---------------------------------------------------------------------------------- | ----------- |
| `AWS_ACCESS_KEY_ID`     | The AWS access key ID that has GetObject, and optionally ListBucket, permissions   | _not shown_ |
| `AWS_SECRET_ACCESS_KEY` | The secret part of the AWS access key                                              | _not shown_ |
| `KEY_PREFIX`            | A folder-like prefix to be prepended to all object keys. No slashes should be used | `my-folder` |
| `SSO_URL_INTERNAL`            | A URL for the app to use when connecting directly to the SSO server. Defaults to `SSO_URL` if not specified. Mainly useful for dev. | `https://sso.domain.com/` |

The following optional ENV vars are used to control and configure use of the Minio and SSO mock containers; useful in dev if you don't want to (or can't) connect to live services from a local machine.

| Variable                | Description                                                                        | Example     |
| ----------------------- | ---------------------------------------------------------------------------------- | ----------- |
| `S3_USE_LOCAL`            | A boolean that sets boto3 config in the main app to connect to Minio using an endpoint rather than default S3 endpoint generation. Defaults to `False`. | `True` |
| `S3_ENDPOINT_URL`            | An endpoint URL (including schema and port) for the app to use when connecting to the local Minio server. Only inspected if `S3_USE_LOCAL` is `True`. | `http://minio:9000` |
| `SSO_URL_INTERNAL`            | A URL for the app to use when connecting directly to the SSO server. Defaults to `SSO_URL` if not specified. | `http://sso:8001/` |

## Notes on functionality

### Permissions and 404s

If the AWS user/role has the ListBucket permission, 404s are proxied through to the user to aid debugging.

### Shutdown

On SIGTERM any in-progress requests will complete before the process exits. At the time of writing PaaS will then forcibly kill the process with SIGKILL if it has not exited within 10 seconds.

### Range requests

The headers `range`, `content-range` and `accept-ranges` and proxied to allow range requests. This means that video should be able to be proxied with reasonable seeking behaviour.

### Parallel flows with new sessions

Parallel requests for users that have no existing cookies are supported

### Key-limitation

The path `/__redirect_from_sso` is used as part of SSO authentication. This corresponds to the key `__redirect_from_sso`, and so the object with this key cannot be proxied.

## Running locally

Ensure you have a docker daemon running and available. Note that by default your local environment will be self-contained; update your local ENV vars to override this behaviour.

* Copy the example env file cp .env.example .env
* Configure env vars (talk to SRE for values) - or use as-is, connecting to the local minio container instead of S3 and a local SSO mock instead of a live one
* Build local docker instance:
  * `make build`
* Start the local docker instance:
  * `make up`
* Open a browser at http://localhost:8000/<object_key>
* Edit your code locally as normal

> Please note that the SSO mock is very limited in the way that it behaves. It may be useful while developing or debugging other functionality, but don't rely on it behaving as a real SSO service would.

### Adding dependencies

* Run `make bash` to open a console to a new container witht he app code.
* Use poetry commands to add your dependeny - e.g. `poetry add boto3` - verify that your `pyproject.toml` file is updated
* Run `poetry install` on your group if necessary, to generate the local `poetry.lock` file
* `exit` your bash console, shutting down the temporary container
* `make build` to generate a new docker image containing the updated deps - this is because the poetry install command is in the Dockerfile
* `make up` to continue working in a full environment containing your new dependencies
* `make reload` after changing your `app.py` file to reload the app container without running a docker build, or `make rebuild` if you need your changes to be built

## Running tests

Ensure you have a docker daemon running and available, and that you have installed the `testing` dependencies via poetry.

Once you have the docker containers running locally (see above) simply `make test`

> Note that some tests require specific responses from the SSO mock; you're best to start with a freshly run sso container rather than one that's run tests already or you'll get FAIL or ERROR responses unexpectedly.
