#!/usr/bin/python
import os
import argparse
from urllib import parse, request
import requests
import mimetypes
import warnings

from pdfminer.high_level import extract_text

from gdrive_utils import add_text_to_gdrive
from pocket_utils import authorize_pocket, add_links_to_pocket


MAX_TAG_LENGTH = 25

# A utility to help with checking extension and downloading inputted filepath
# Adapted rom https://stackoverflow.com/questions/15203829/python-argparse-file-extension-checking
def ProcessFilepath(extensions):
    class Act(argparse.Action):
        def ext_ok(self, extension, parser, option_string):
            if extension not in extensions:
                option_string = "({})".format(option_string) if option_string else ""
                parser.error(
                    "file doesn't end with one of {}{}".format(
                        extensions, option_string
                    )
                )
            else:
                return True

        def __call__(self, parser, namespace, fpath, option_string=None):
            # Check whether the path is a local path or a URL
            if parse.urlparse(fpath).scheme == "":
                # Path is a local path
                extension = os.path.splitext(fpath)[1][1:]
                assert self.ext_ok(extension, parser, option_string)
                setattr(namespace, self.dest, fpath)
            else:  # fpath is a URL
                url = fpath
                # Get the file
                with requests.get(url, stream=True) as response:
                    # Validate the extension
                    content_type = response.headers["content-type"]
                    # Get extension type and remove '.' from e.g. '.pdf'
                    extension = mimetypes.guess_extension(content_type)[1:]
                    assert self.ext_ok(extension, parser, option_string)
                    fname = "/tmp/pdf_to_pocket/downloaded_file" + "." + extension
                    print(f"Downloading from {url}.")
                    request.urlretrieve(url, fname)

                    print(f"File downloaded to {fname}.")
                    setattr(namespace, self.dest, fname)

    return Act


parser = argparse.ArgumentParser(description="Process and upload a file into Pocket.")
parser.add_argument("docname", help="The name to give the document in gdrive/pocket")
parser.add_argument(
    "filename",
    action=ProcessFilepath(["pdf", "epub"]),
    help="The path to the file being processed, either local or a URL; file must be of type *.pdf or *.epub",
)
parser.add_argument(
    "-t",
    "--tag",
    dest="tag_name",
    type=lambda x: x
    if all([len(a) <= MAX_TAG_LENGTH for a in x.split(", ")])
    else False,  # Sample Function
    help="The Tag to assign to all generated Pocket articles. NOTE: tags must be at most 25 chars, and separated by ' ,'",
    default=None,
)
parser.add_argument(
    "-wpf",
    "--words-per-file",
    dest="words_per_file",
    type=int,
    default=20000,
    help="Number of words to include in each uploaded fragment",
)
parser.add_argument(
    "-p",
    "--preview",
    dest="preview",
    action="store_true",
    help="Whether to show the user a draft text file in an editor before uploading it to pocket.",
)
parser.add_argument(
    "--edit-only",
    dest="edit_only",
    action="store_true",
    help="Whether to terminate the program after the text parsing stage.",
)
parser.add_argument(
    "--ignore-default-tag",
    "-idt",
    dest="ignore_default_tag",
    action="store_true",
    help='Whether to exclude the default "pdf-to-pocket" pocket tag',
)
# TODO Add argument to "preview" text before adding to pocket
os.makedirs("/tmp/pdf_to_pocket/", exist_ok=True)
args = parser.parse_args()
filename = args.filename
doc_name = args.docname
if args.tag_name is None:
    if len(doc_name) > MAX_TAG_LENGTH:
        warnings.warn(
            "Doc name is too long and no tag name indicated, so no custom tag will be provided to pocket."
        )
        tag_name = ""
    else:
        tag_name = doc_name
else:
    tag_name = args.tag_name
if not args.ignore_default_tag:
    tag_name += ", pdf-to-pocket"
words_per_file = args.words_per_file

# Verify that you have Pocket and Google credentials
with open("pocket_api_key.txt", "r") as f:
    pocket_api_key = f.read()

assert os.path.exists(
    "gdrive_credentials.json"
), "Must get a gdrive credentials file; for more info, click on 'Enable Drive API' at https://developers.google.com/drive/api/v3/quickstart/python "

# Extract the text
extension = os.path.splitext(filename)[1][1:]
print("Extracting text")
if extension == "pdf":
    text = extract_text(filename)
print("Text extracted!")

if args.preview:
    import subprocess

    textfile = "/tmp/pdf_to_pocket/preview.txt"
    if os.path.exists(textfile):
        os.remove(textfile)
    with open(textfile, "w") as f:
        f.write(text)

    p = subprocess.Popen(f"{os.environ['EDITOR']} {textfile}", shell=True)
    print("When you're done editing, close the window and we'll resume.")
    p.wait()
    if args.edit_only:
        exit("Terminating without uploading docs.")
    with open(textfile, "r") as f:
        text = f.read()
    print("Resuming!")

print("Uploading to gdrive")
pubd_gdrive_links, gdrive_names = add_text_to_gdrive(
    text, doc_name, "gdrive_credentials.json", max_words_per_file=words_per_file
)
print("Links: ", pubd_gdrive_links)

access_token = authorize_pocket(pocket_api_key, tag_name)
add_links_to_pocket(
    pubd_gdrive_links, gdrive_names, tag_name, pocket_api_key, access_token,
)
