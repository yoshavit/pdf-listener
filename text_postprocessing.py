import os
import subprocess

from getch import getch


def postprocess_text(raw_text, filename, config):
    fname = os.path.split(filename)[1].split(".")[0]  # get file name w/o ext
    if config.show_diff:
        # save unprocessed file
        raw_textfile = "/tmp/pdf_to_pocket/{}_unprocd.txt".format(fname)
        if os.path.exists(raw_textfile):
            os.remove(raw_textfile)
        with open(raw_textfile, "w") as f:
            f.write(raw_text)

    text = postprocess_text_content(raw_text, config)
    textfile = "/tmp/pdf_to_pocket/{}.txt".format(fname)
    if os.path.exists(textfile):
        os.remove(textfile)
    with open(textfile, "w") as f:
        f.write(text)

    if config.show_diff:
        p = subprocess.Popen("diff -y {} {}".format(raw_textfile, textfile), shell=True)
        print("Once you've closed the diff, we'll resume")
        p.wait()
        print("To abort, press 'q'. To continue, press any other key.")
        key = getch()
        if key == "q":
            exit("Script aborted after diff")

    if config.edit:
        p = subprocess.Popen("{} {}".format(os.environ["EDITOR"], textfile), shell=True)
        print("When you're done editing, close the window and we'll resume.")
        p.wait()
        with open(textfile, "r") as f:
            text = f.read()
        print("Resuming!")

    return text


def postprocess_text_content(text, config):
    return text
