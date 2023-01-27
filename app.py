import gevent  # type: ignore noqa
from gevent import (  # type: ignore noqa
    monkey,
)

monkey.patch_all()  # noqa type: ignore

import requests
import redis
from gevent.pywsgi import (
    WSGIHandler,
    WSGIServer,
)
from flask import (
    Flask,
    Response,
    request,
)
import urllib.parse
import sys
import signal
import secrets
import os
import json
import logging
import hmac
import hashlib
from functools import (  # type: ignore
    wraps,
)
from datetime import (
    datetime,
)
import boto3
from botocore.config import Config


def camel_to_pascal_case(input):
    """Needed for the boto dict keys and param names, vs header names"""
    return input.replace("_", " ").title().replace(" ", "")


def get_boto_s3client_args(
    aws_access_key_id=None, aws_secret_access_key=None, aws_region=None
):
    """Extracted to a function to allow monkey-patching for test run"""
    boto_config = Config(
        signature_version="v4", retries={"max_attempts": 10, "mode": "standard"}
    )

    args = ("s3",)
    kwargs = {
        "config": boto_config,
        "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        # "aws_region":'us-east-1',
        "endpoint_url": 'http://minio:9000', # @TODO make this for local dev only
    }
    if aws_access_key_id is not None:
        kwargs["aws_access_key_id"] = aws_access_key_id
    if aws_secret_access_key is not None:
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    if aws_region is not None:
        kwargs["region_name"] = aws_region
    return args, kwargs


def proxy_app(
    logger,
    port,
    redis_url,
    sso_url,
    sso_client_id,
    sso_client_secret,
    bucket,
    aws_region,
    healthcheck_key,
    sso_url_internal,
    key_prefix=None,
    aws_access_key_id=None,
    aws_secret_access_key=None,
):

    proxied_request_headers = [
        "range",
    ]
    proxied_response_headers = [
        "accept-ranges",
        "content-length",
        "content-type",
        "date",
        "etag",
        "last-modified",
        "content-range",
    ]
    redis_prefix = "s3proxy"
    redis_client = redis.from_url(redis_url)

    if key_prefix is not None:
        key_prefix += "/"
    else:
        key_prefix = ""

    boto_args, boto_kwargs = get_boto_s3client_args(
        aws_access_key_id, aws_secret_access_key, aws_region
    )
    s3 = boto3.client(*boto_args, **boto_kwargs)

    def start():
        server.serve_forever()

    def stop(_, __):
        server.stop()

    def authenticate_by_sso(f):
        auth_path = "o/authorize/"
        token_path = "o/token/"
        me_path = "api/v1/user/me/"
        grant_type = "authorization_code"
        scope = "read write"
        response_type = "code"

        redirect_from_sso_path = "/__redirect_from_sso"

        session_cookie_name = "assets_session_id"
        session_state_key_prefix = "sso_state"
        session_token_key = "sso_token"

        expired_message = (
            b'<p style="font-weight: bold; font-family: Helvetica, Arial, sans-serif">'
            b"Sign in may have taken too long. Please try the original link again."
            b"</p>"
        )

        cookie_max_age = 60 * 60 * 9
        redis_max_age_session = 60 * 60 * 10
        redis_max_age_state = 60

        @wraps(f)
        def _authenticate_by_sso(*args, **kwargs):

            if request.path == f"/{healthcheck_key}":
                logger.debug("Allowing healthcheck")
                return f(*args, **kwargs)

            logger.debug("Authenticating %s", request)

            def get_session_value(key):
                session_id = request.cookies[session_cookie_name]
                return redis_get(f"{session_cookie_name}__{session_id}__{key}")

            # In our case all session values are set exactly when we want a new session cookie
            # (done to mitigate session fixation attacks)
            def with_new_session_cookie(response, session_values):
                session_id = secrets.token_urlsafe(64)
                response.set_cookie(
                    session_cookie_name,
                    session_id,
                    httponly=True,
                    secure=request.headers.get("x-forwarded-proto", "http") == "https",
                    max_age=cookie_max_age,
                    expires=datetime.utcnow().timestamp() + cookie_max_age,
                )
                for key, value in session_values.items():
                    redis_set(
                        f"{session_cookie_name}__{session_id}__{key}",
                        value,
                        redis_max_age_session,
                    )

                return response

            def get_callback_uri():
                scheme = request.headers.get("x-forwarded-proto", "http")
                return f"{scheme}://{request.host}{redirect_from_sso_path}"

            def get_request_url_with_scheme():
                scheme = request.headers.get("x-forwarded-proto", "http")
                return (
                    f'{scheme}://{request.host}{request.environ["REQUEST_LINE_PATH"]}'
                )

            def redirect_to_sso():
                logger.debug("Redirecting to SSO: {")
                callback_uri = urllib.parse.quote(get_callback_uri(), safe="")
                state = secrets.token_hex(32)
                redis_set(
                    f"{session_state_key_prefix}__{state}",
                    get_request_url_with_scheme(),
                    redis_max_age_state,
                )

                redirect_to = (
                    f"{sso_url}{auth_path}?"
                    f"scope={scope}&state={state}&"
                    f"redirect_uri={callback_uri}&"
                    f"response_type={response_type}&"
                    f"client_id={sso_client_id}"
                )

                return Response(status=302, headers={"location": redirect_to})

            def redirect_to_final():
                try:
                    code = request.args["code"]
                    state = request.args["state"]
                except KeyError:
                    logger.exception("Missing code or state")
                    return Response(b"", 400)

                try:
                    final_uri = redis_get(f"{session_state_key_prefix}__{state}")
                except KeyError:
                    logger.exception("Unable to find state in Redis")
                    return Response(
                        expired_message, 403, headers={"content-type": "text/html"}
                    )

                logger.debug("Attempting to redirect to final: %s", final_uri)

                data = {
                    "grant_type": grant_type,
                    "code": code,
                    "client_id": sso_client_id,
                    "client_secret": sso_client_secret,
                    "redirect_uri": get_callback_uri(),
                }
                with requests.post(f"{sso_url_internal}{token_path}", data=data) as response:
                    content = response.content

                if response.status_code in [401, 403]:
                    logger.debug("token_path response is %s", response.status_code)
                    return Response(b"", response.status_code)

                if response.status_code != 200:
                    logger.debug("token_path error")
                    return Response(b"", 500)

                response = with_new_session_cookie(
                    Response(status=302, headers={"location": final_uri}),
                    {session_token_key: json.loads(content)["access_token"]},
                )
                response.autocorrect_location_header = False
                return response

            def get_token_code(token):
                with requests.get(
                    f"{sso_url_internal}{me_path}", headers={"authorization": f"Bearer {token}"}
                ) as response:
                    return response.status_code

            if request.path == redirect_from_sso_path:
                return redirect_to_final()

            try:
                token = get_session_value(session_token_key)
            except KeyError:
                return redirect_to_sso()

            token_code = get_token_code(token)
            if token_code in [401, 403]:
                logger.debug("token_code response is %s", token_code)
                return redirect_to_sso()

            if token_code != 200:
                return Response(b"", 500)

            return f(*args, **kwargs)

        return _authenticate_by_sso

    @authenticate_by_sso
    def proxy(path):
        logger.debug("Attempt to proxy: %s", request)

        def body_upstream(streamingBody):
            for chunk in streamingBody.iter_chunks(chunk_size=16384):
                yield chunk

        def body_empty(streamingBody):
            # Ensure this is a generator
            while False:
                yield
            for _ in iter(streamingBody):
                pass

        request_kwargs = {"Bucket": bucket, "Key": key_prefix + path}
        for key in proxied_request_headers:
            if key in request.headers:
                request_kwargs[camel_to_pascal_case(key)] = request.headers[key]

        try:
            s3_obj = s3.get_object(**request_kwargs)
            if "Range" in request_kwargs:
                status_code = 206
            else:
                status_code = 200
        except s3.exceptions.NoSuchKey as e:
            status_code = 404
        except:
            status_code = 500

        logger.debug(f"Status code: {status_code}")

        if status_code in (200, 206):
            response_headers = tuple(
                (
                    (key, s3_obj[camel_to_pascal_case(key)])
                    for key in proxied_response_headers
                    if camel_to_pascal_case(key) in s3_obj
                )
            )

            downstream_response = Response(
                body_upstream(s3_obj["Body"]),
                status=status_code,
                headers=response_headers,
            )
            downstream_response.call_on_close(s3_obj["Body"].close)
        else:
            downstream_response = Response(body_empty([]), status=status_code)
        return downstream_response

    def redis_get(key):
        value_bytes = redis_client.get(f"{redis_prefix}__{key}")
        if value_bytes is None:
            raise KeyError(key)
        return value_bytes.decode()

    def redis_set(key, value, ex):
        redis_client.set(f"{redis_prefix}__{key}", value.encode(), ex=ex)

    class RequestLinePathHandler(WSGIHandler):
        # The default WSGIHandler does not preseve a trailing question mark
        # from the original request-line path sent by the client
        def get_environ(self):
            return {
                **super().get_environ(),
                "REQUEST_LINE_PATH": self.path,
            }

    app = Flask("app")

    app.add_url_rule("/", view_func=proxy, defaults={"path": "/"})
    app.add_url_rule("/<path:path>", view_func=proxy)
    server = WSGIServer(("0.0.0.0", port), app, handler_class=RequestLinePathHandler)

    return start, stop


def main():
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    start, stop = proxy_app(
        logger,
        int(os.environ["PORT"]),
        json.loads(os.environ["VCAP_SERVICES"])["redis"][0]["credentials"]["uri"],
        os.environ["SSO_URL"],
        os.environ["SSO_CLIENT_ID"],
        os.environ["SSO_CLIENT_SECRET"],
        os.environ["AWS_S3_BUCKET"],
        os.environ["AWS_DEFAULT_REGION"],
        os.environ["AWS_S3_HEALTHCHECK_KEY"],
        os.environ.get("SSO_URL_INTERNAL", os.environ["SSO_URL"]),
        os.environ.get("KEY_PREFIX", None),
        os.environ.get("AWS_ACCESS_KEY_ID", None),
        os.environ.get("AWS_SECRET_ACCESS_KEY", None),
    )

    gevent.signal.signal(signal.SIGTERM, stop)
    start()
    gevent.get_hub().join()


if __name__ == "__main__":
    main()
