import os
import requests
from urllib.parse import urlencode, parse_qs
import webbrowser

from tqdm import tqdm

from getch import getch


def authorize_pocket(api_key, tag_name):
    """Get access token to interact with Pocket app
    """

    # Let's follow the authorization steps from:
    # https://getpocket.com/developer/docs/authentication

    # Step 1: Get request token
    redirect_uri = f"https://app.getpocket.com/tags/{tag_name}/all"
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
    # TODO: create a simple Django page for the user to click a button
    # For now, we'll just ask the user to hit enter on the command line
    _wait_for_acknowledgement()

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
    # Reversed order so that first uploads are last
    urls_r = reversed(urls)
    if verbose:
        print("Uploading URLs to pocket")
        iterator = tqdm(enumerate(urls_r))
    else:
        iterator = enumerate(urls_r)

    for i, url in iterator:
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


def _wait_for_acknowledgement():
    try:
        print(
            "Press any key to confirm you've clicked through the authorization, or press ctrl-c to cancel."
        )

        key = getch()
    except:
        raise EOFError("Cancelled upload.")
