## Clone the repo

Clone this repo into your directory of choice:

```
git clone https://github.com/yoshavit/pdf-listener.git
```

## Install dependencies

Make sure you have Python 3.6 or later, and run the following to install dependencies.

```
pip install --upgrade pdfminer.six bottle google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Acquire credentials

### Acquire Google Drive credentials

To be able to upload our documents to GDrive and publish them (allowing Pocket to read them),
we need to setup Google Drive credentials.

<!-- Follow the steps under "Creating API Keys" on this page:
https://developers.google.com/maps/documentation/directions/get-api-key -->

<!-- Go to https://console.cloud.google.com/projectselector2/home/dashboard , and accept the terms of service. -->

Go to https://developers.google.com/drive/api/v3/quickstart/python, and click on `Enable the Drive API`.
Under "New project name", put something simple like `PDFListener`. At "Configure your OAuth client", select `Desktop App`.

Now, click on `Download Client Configuration`. This should download a `credentials.json` file.

Now place this file into our directory. Assuming you're still in the repo's local directory, call

```
mv ~/Downloads/credentials.json .
```

<!-- Create a new project (call it whatever you like; `PDFListener` works fine). No need to specify the organization.
Once the project is set up, you should now be on the project's page.

Next, under the API card, click `go to APIs Overview`. At the top, click `Enable APIs and Services`. Search for `drive`, and click on the `Google Drive API`. Then click `Enable`.

Now, on the top right of the page, click the button `Create Credentials`. Under `Which API are you using?` select `Google Drive API`. Under `Where will you be calling the API from?` select `Other UI (e.g. Windows, CLI tool)`. Under `What data will you be accessing?`, select only `Application data`. Finally, click on `What credentials do I need`.

Under `Service Account Name` write something, like `Admin`. For `Role`, select `Project -> Owner`. Then select the JSON key type, and click Continue. -->

### Pocket API Key

To be able to add our files to Pocket, we're going to need a Pocket API key.

Go to https://getpocket.com/developer/apps/new.
Under application name, put a custom name, like `pdflistener_[your_name]`.
Under application description, write something like `Listen to custom content I upload.`.

Under "Permissions", check only "Add".

Under "Platforms", check only "Desktop (Other)".

Accept the terms of service, and then click "Create Application".

You'll be navigated to the "My Applications" page, where, next to the application name you provided,
you should see a consumer key (e.g. `12345-abcd67890beef1337`). Highlight and copy the text of the key.

Now, open `./pocket_api_key.py` in this repo. Remove the currentl value of `pocket_api_key`. Paste in your API key instead, in quotes.

You should be ready!
