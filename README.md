# PDF Listener

This is a project to allow anyone to listen to PDFs as "podcasts", by leveraging [the Pocket App](https://getpocket.com/)'s "Listen to Article View" feature.

### How it works

You use Pocket by adding links to articles, to be read later. Each time you add a link, Pocket attempts to parse the contents of a link into its special "Article View" format. If it succeeds, as it does for e.g. the NYT or other compatible webpages,
then it unlocks additional features for that article in the app. In particular, Pocket can [use your device's built-in text-to-speech capabilities](https://help.getpocket.com/article/1081-listening-to-articles-in-pocket-with-text-to-speech).

All we need to do to make Pocket read out our PDFs is to provide them in an "Article View" compatible format.
Thankfully, published Google Docs links can be parsed into Article View, provided they aren't too long!

To load a PDF file into Pocket, our script will:

1. (If necessary) Download the PDF.
2. Convert the PDF to text using `pdfminer.six`, and clean it a little (see `text_postprocessing.py`).
3. Upload the text to Google Docs (in multiple files if it's long), and publish it to the open web.
4. Add each of these files to Pocket, along with any relevant tags.

## Setup

First, if you don't have a Pocket account, [create one here](https://getpocket.com/).
I'd also strongly recommend downloading the Pocket app on your phone, so you can listen to files on the go.

If you don't have a Google account, bravo. That can't be easy.

### Clone the repo

Clone this repo into your directory of choice:

```bash
$ git clone https://github.com/yoshavit/pdf-listener.git
```

### Install dependencies

Make sure you have Python 3.6 or later, and run the following to install dependencies.

```bash
$ pip install --upgrade pdfminer.six bottle google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Acquire Google Drive credentials

To be able to upload our documents to Google Drive and publish them (allowing Pocket to read them),
we need to setup Google Drive credentials.

<!-- Follow the steps under "Creating API Keys" on this page:
https://developers.google.com/maps/documentation/directions/get-api-key -->

<!-- Go to https://console.cloud.google.com/projectselector2/home/dashboard , and accept the terms of service. -->

Go to https://developers.google.com/drive/api/v3/quickstart/python, and click on `Enable the Drive API`.
Under "New project name", put something simple like `PDFListener`. At "Configure your OAuth client", select `Desktop App`.

Now, click on `Download Client Configuration`. This should download a `credentials.json` file.

Now place this file into our directory.

```bash
$ cd path/to/cloned/directory
$ mv ~/Downloads/credentials.json .
```

<!-- Create a new project (call it whatever you like; `PDFListener` works fine). No need to specify the organization.
Once the project is set up, you should now be on the project's page.

Next, under the API card, click `go to APIs Overview`. At the top, click `Enable APIs and Services`. Search for `drive`, and click on the `Google Drive API`. Then click `Enable`.

Now, on the top right of the page, click the button `Create Credentials`. Under `Which API are you using?` select `Google Drive API`. Under `Where will you be calling the API from?` select `Other UI (e.g. Windows, CLI tool)`. Under `What data will you be accessing?`, select only `Application data`. Finally, click on `What credentials do I need`.

Under `Service Account Name` write something, like `Admin`. For `Role`, select `Project -> Owner`. Then select the JSON key type, and click Continue. -->

### Acquire Pocket API Key

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

## Usage

### Uploading a PDF

```bash
$ python pdf_listener 'short title for file' https://the.path.to/the/file.pdf
```

TODO Explain CLI options

### Customization

TODO: explain how to add new text postprocessing features

### TODO - Clearing Uploaded Files from Google Drive

## Misc

Pocket is offering us a really wonderful service. They're also owned by Mozilla, and so they're doing ethical work on a shoestring budget. I personally think it'd be pretty cool if, were this to become useful to you, you'd consider [purchasing a premium subscription](https://getpocket.com/premium).

To be clear, I'm not affiliated with Pocket in any way. I think it's really cool that they've made such an excellent text-to-speech feature free to the public. I also maybe worry a little about what this will do to their server costs. Anyway, [help them out](https://getpocket.com/premium) if you can. It's \\$5/mo or \\$45/yr.

Credit originally goes to [Rob Wiblin](http://www.robwiblin.com/) for mentioning this hack with Google Drive and Pocket on his excellent podcast, [The 80,000 Hours Podcast](https://80000hours.org/podcast/).
It's provided me with a lot of helpful career advice, and maybe it'll help you too.

## Development

Pull-requests very welcome!
