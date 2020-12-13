# pocket-from-pdf

A repo to convert PDFs to text, publish that text online, and have Pocket register it.

## Mac

We'll need to install `poppler-utils`.

First, install Homebrew. Then, run:

```
brew install poppler-utils
```

This will let us run `pdftotext`.

Dependencies:
poppler-utils

python:
tqdm, pdfminer.six
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Optional: install/prettify diff
