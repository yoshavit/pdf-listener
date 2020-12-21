import os
import requests
from urllib.parse import urlencode, parse_qs
import webbrowser
import threading

import bottle


LOCAL_SERVER_PORT = 8765


def authorize_pocket(api_key, tag_name):
    """Get access token to interact with Pocket app
    """

    # Let's follow the authorization steps from:
    # https://getpocket.com/developer/docs/authentication

    # Step 1: Get request token
    redirect_uri = f"http://localhost:{LOCAL_SERVER_PORT}/complete"
    response = requests.post(
        "https://getpocket.com/v3/oauth/request",
        data={"consumer_key": api_key, "redirect_uri": redirect_uri,},
    )
    _handle_pocket_status_code(response.status_code)
    # Need to reformat to read type application/x-www-form-urlencoded
    request_token = parse_qs(response.content)["code".encode("utf-8")][0].decode()
    # Step 2: Redirect user to authentication page

    webbrowser.open_new_tab(
        f"https://getpocket.com/auth/authorize?request_token={request_token}&redirect_uri={redirect_uri}"
    )
    # Steps 3 happens outside of Python
    # Step 4: Receive acknowledgement of user authentication
    listen_for_success_uri()

    # Step 5: Convert request_token to access_token
    response = requests.post(
        "https://getpocket.com/v3/oauth/authorize",
        data={"consumer_key": api_key, "code": request_token},
    )
    _handle_pocket_status_code(response.status_code)
    # Need to reformat to read type application/x-www-form-urlencoded
    access_token = parse_qs(response.content)["access_token".encode("utf-8")][
        0
    ].decode()
    return access_token


def _handle_pocket_status_code(status_code):
    if status_code == 200:
        return True
    elif status_code == 400:
        raise RuntimeError(
            "400 - Invalid request, please make sure you follow the documentation for proper syntax"
        )
    elif status_code == 401:
        raise RuntimeError("401 - Problem authenticating the user")
    elif status_code == 403:
        raise RuntimeError(
            "403 - User was authenticated, but access denied due to lack of permission or rate limiting"
        )
    elif status_code == 503:
        raise RuntimeError(
            "503 - Pocket's sync server is down for scheduled maintenance."
        )
    elif "50" in str(status_code):
        raise RuntimeError(f"{status_code} - Some sort of Pocket server issue.")
    else:
        raise RuntimeError(f"Pocket returned unknown status code: {status_code}")


def add_links_to_pocket(
    urls, file_names, tag_name, api_key, access_token, verbose=True,
):
    if verbose:
        print("Uploading URLs to pocket...")

    # Reversed order so that first uploads are last
    for i, url in enumerate(reversed(urls)):
        response = requests.post(
            "https://getpocket.com/v3/add",
            data={
                "url": url,
                "title": file_names[i],
                "tags": tag_name,
                "consumer_key": api_key,
                "access_token": access_token,
            },
        )
        _handle_pocket_status_code(response.status_code)
    if verbose:
        print("Files uploaded to pocket!")


def listen_for_success_uri():
    """Construct a simple server that terminates when a request is called to its '/complete' page
    We will then pass the URI pointing to this server to Pocket, which will call it upon successful oauth,
    confirming to our script that Pocket authorization has occurred
    """
    trigger = threading.Event()
    print("Listening for Pocket authorization...")

    server = MyServer(port=LOCAL_SERVER_PORT, host="localhost")

    @bottle.route("/complete")
    def process():
        trigger.set()
        return "Pocket access authorized! You can now close this window."

    def begin():
        bottle.run(server=server, quiet=True)

    thread = threading.Thread(target=begin)
    # http://localhost:8765/complete
    thread.start()
    if not trigger.wait(timeout=600):  # seconds
        raise RuntimeError(
            "Authorization wasn't provided after 10 minutes, so the Pocket upload was cancelled."
        )
    server.shutdown()

    print("Authorization received!")


class MyServer(bottle.WSGIRefServer):
    def run(self, app):  # pragma: no cover
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
        from wsgiref.simple_server import make_server
        import socket

        class FixedHandler(WSGIRequestHandler):
            def address_string(self):  # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(self2, *args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(self2, *args, **kw)

        handler_cls = self.options.get("handler_class", FixedHandler)
        server_cls = self.options.get("server_class", WSGIServer)

        if ":" in self.host:  # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, "address_family") == socket.AF_INET:

                class server_cls(server_cls):
                    address_family = socket.AF_INET6

        srv = make_server(self.host, self.port, app, server_cls, handler_cls)
        self.srv = srv  ### THIS IS THE ONLY CHANGE TO THE ORIGINAL CLASS METHOD!
        srv.serve_forever()

    def shutdown(self):  ### ADD SHUTDOWN METHOD.
        self.srv.shutdown()
        # self.server.server_close()
