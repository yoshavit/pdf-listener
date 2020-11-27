import pickle
import os.path
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_NAME = "pdf-to-pocket"
LOCAL_FOLDER_NAME = "/tmp/pdf_to_pocket/"

# TODO handle HTTP error codes gracefully


def add_text_to_gdrive(text, name, credentials_file, max_words_per_file=None):
    """Takes text and uploads it to a dedicated folder
    in Google Drive
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # This is the google drive API object
    drive_service = build("drive", "v3", credentials=creds)

    # Find the pdf-to-pocket file, or create one if it doesn't exist
    results = (
        drive_service.files()
        .list(
            q=f"name = '{FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'",
            spaces="drive",
        )
        .execute()
    )
    items = results.get("files", [])
    if items:
        drive_folder = items[0]
    if not items:
        print("No pdf-to-pocket fodler found; creating one.")
        results = (
            drive_service.files()
            .create(
                body={
                    "name": f"{FOLDER_NAME}",
                    "mimeType": "application/vnd.google-apps.folder",
                    "folderColorPalette": "#D86262",
                }
            )
            .execute()
        )
        drive_folder = results.get("files", [])[0]

    # Build the text file into a series of files if necessary
    text_fragments = []
    if max_words_per_file:
        remaining_split = text.split(" ")
        while len(remaining_split) > max_words_per_file:
            fragment_split = remaining_split[:max_words_per_file]
            fragment = " ".join(fragment_split)
            text_fragments.append(fragment)
            remaining_split = remaining_split[max_words_per_file:]
        else:
            text_fragments.append(" ".join(remaining_split))
    else:
        text_fragments = [text]

    # Create a local file directory
    os.makedirs(LOCAL_FOLDER_NAME, exist_ok=True)

    # Create a remote file directory
    results = (
        drive_service.files()
        .create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [drive_folder["id"]],
            }
        )
        .execute()
    )
    text_folder_id = results["id"]

    # Upload each of the files
    published_drive_links = []
    file_names = []
    for idx, text_fragment in enumerate(text_fragments, start=1):
        if len(text_fragments) > 1:
            title = name + " -- Part {}".format(idx)
        else:
            title = name

        # Create a file locally
        filename = LOCAL_FOLDER_NAME + title + ".txt"
        with open(filename, "w") as f:
            f.write(text_fragment)

        # Upload that file to the folder
        file_metadata = {
            "name": title,
            "parents": [text_folder_id],
            "mimeType": "application/vnd.google-apps.document",
        }
        media = MediaFileUpload(filename, mimetype="text/plain")
        file = (
            drive_service.files().create(body=file_metadata, media_body=media).execute()
        )

        # Make sure each file is published to the web
        results = drive_service.revisions().list(fileId=file["id"]).execute()
        # Since we've just created this file, there should only be one revision
        revision = results["revisions"][0]
        # There's no natively-implemented python "update" Http request,
        # so we'll post one the old fashioned way
        response = (
            drive_service.revisions()
            .update(
                fileId=file["id"],
                revisionId=revision["id"],
                body={
                    "published": True,
                    "autoPublish": True,
                    "publishedOutsideDomain": True,
                },
            )
            .execute()
        )
        # According to https://stackoverflow.com/questions/59148718/google-drive-api-publish-document-and-get-published-link
        # the following is how to access published drive links
        published_drive_links.append(
            f"https://docs.google.com/document/d/{file['id']}/pub"
        )
        file_names.append(filename)

    return published_drive_links, file_names

