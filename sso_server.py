# flake8: noqa
import gevent  # type: ignore # noqa
from gevent import monkey  # type: ignore # noqa

monkey.patch_all()  # noqa # type: ignore

import json
import logging
import os
import signal
import socket
import sys
import time
from multiprocessing import Process

from flask import Flask, Response, request


def create_sso(
    logger,
    port,
    max_attempts=100,
    is_logged_in=True,
    client_id="the-client-id",
    client_secret="the-client-secret",  # PS-IGNORE
    tokens_returned=None,  # None => infinite (see below), override for other behaviours
    token_expected="the-token",
    code_returned="the-code",
    code_expected="the-code",
    me_response_code=200,
):
    # Mock SSO in a different container using defn written in test file, to allow easy local debugging

    def start():
        app = Flask("app")
        app.add_url_rule("/api/v1/user/me/", view_func=handle_me, methods=["GET"])
        app.add_url_rule("/o/authorize/", view_func=handle_authorize, methods=["GET"])
        app.add_url_rule("/o/token/", view_func=handle_token, methods=["POST"])

        def _stop(_, __):
            sys.exit()

        signal.signal(signal.SIGTERM, _stop)

        try:
            app.run(host="0.0.0.0", port=port, debug=True)
        except SystemExit:
            # app.run doesn't seem to have a good way of killing the server,
            # and want to exit cleanly for code coverage
            pass

    def wait_until_connected():
        for i in range(0, max_attempts):
            try:
                with socket.create_connection(("0.0.0.0", port), timeout=0.1):
                    break
            except (OSError, ConnectionRefusedError):
                if i == max_attempts - 1:
                    raise
                time.sleep(0.01)

    def stop():
        process.terminate()
        process.join()

    def handle_me():
        correct = request.headers.get("authorization", "") == f"Bearer {token_expected}"
        me = {
            "email": "test@test.com",
            "first_name": "Peter",
            "last_name": "Piper",
            "user_id": "7f93c2c7-bc32-43f3-87dc-40d0b8fb2cd2",
        }
        return (
            Response(json.dumps(me), status=me_response_code)
            if correct
            else Response(status=403)
        )

    def handle_authorize():
        args = request.args
        redirect_url = (
            f'{args["redirect_uri"]}' f'?state={args["state"]}&code={code_returned}'
        )
        return (
            Response(status=302, headers={"location": redirect_url})
            if is_logged_in
            else Response(b"The login page", status=200)
        )

    # unlimited supply of valid tokens by default
    class Tokens:
        def __iter__(self):
            return self

        def __next__(self):
            return "the-token"

    if tokens_returned is None:
        tokens_returned = Tokens()

    token_iter = iter(tokens_returned)

    def next_token():
        nonlocal token_iter
        try:
            return next(token_iter)
        except StopIteration:
            iter(tokens_returned)
            return next(token_iter)

    def handle_token():
        correct = (
            request.form["code"] == code_expected
            and request.form["client_id"] == client_id
            and request.form["client_secret"] == client_secret
            and request.form["grant_type"] == "authorization_code"
        )
        return (
            Response(json.dumps({"access_token": next_token()}), status=200)
            if correct
            else Response(status=403)
        )

    process = Process(target=start)
    process.start()

    return wait_until_connected, stop


def main():
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    start, stop = create_sso(
        logger,
        int(os.environ["PORT"]),
    )

    gevent.signal.signal(signal.SIGTERM, stop)
    start()
    gevent.get_hub().join()


if __name__ == "__main__":
    main()
