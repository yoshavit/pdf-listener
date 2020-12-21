import os
import subprocess
import re
from shlex import quote

MIN_PREFIX_LENGTH = 10


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
        p = subprocess.Popen(
            "git diff --no-index {} {}".format(quote(raw_textfile), quote(textfile)),
            shell=True,
        )
        print("Resuming after diff closed...")
        p.wait()

    if config.edit:
        p = subprocess.Popen(
            "{} {}".format(os.environ["EDITOR"], quote(textfile)), shell=True
        )
        print("When you're done editing, close the window and we'll resume.")
        p.wait()
        with open(textfile, "r") as f:
            text = f.read()
        print("Resuming!")

    return text


def postprocess_text_content(raw_text, config):
    pages = raw_text.split("\f")
    pages = remove_trailing_blank_pages(pages)
    pages = remove_sub_and_superscripts(pages)
    pages = remove_page_numbers(pages)
    pages = remove_border_text(pages, top=True)
    pages = remove_border_text(pages, top=False)
    text = "\f".join(pages)
    return text


def remove_page_numbers(pages):
    numbers_in_pages = extract_ints(pages)
    candidates = set({})  # initial_num: intial_page
    # We're going to keep track of the numbers that appear, and drop only the ones
    # that increment on each page until the end.
    HIGHEST_ALLOWED_STARTING_PAGE = 20
    # Sometimes numbers start after the first page, so the above
    # defines how many pages in to look for the start of a page number sequence
    for current_page_num, (page_str, numbers) in enumerate(
        zip(pages, numbers_in_pages)
    ):
        # first, update to check whether each number is the continuation of an existing sequence
        new_candidates = set({})
        for n in numbers:
            for (initial_num, initial_page) in candidates:
                if n == initial_num + current_page_num - initial_page:
                    new_candidates.add((initial_num, initial_page))
                    break
            else:  # not a continuation
                if current_page_num < HIGHEST_ALLOWED_STARTING_PAGE:
                    new_candidates.add((n, current_page_num))
        candidates = new_candidates
    if len(candidates) == 0:
        # this suggests no page numbers
        # WARNING: if the last page happens to have no page numbers, this will fail to pick up any page numbers
        return pages
    # Pick the number starting at the earliest page, i.e. the longest running number sequence, as page numbers
    first_pn, first_pn_page = min(candidates, key=lambda x: x[1])

    # Next, let's remove these numbers from all the pages
    processed_pages = pages[:first_pn_page]
    for i, page in enumerate(pages[first_pn_page:]):
        # remove all occurrences of the page number
        new_page = re.sub(r"(\s+)({})(\s+|$)".format(str(first_pn + i)), r"\1\3", page)
        processed_pages.append(new_page)
    return processed_pages


def remove_border_text(pages, top=True):
    # Find the longest frequently-occurring prefixes/suffixes and delete them out
    # You might wonder why we don't just pick the single longest
    # The answer is that sometimes pdfs alternate between 2 page types, and we'd like to remove the prefixes from both
    n = len(pages)
    # on what fraction of pages must a phrase occur for us to call it a prefix?
    # (This is important to prevent accidentally removing common phrases)
    if n == 1:
        # no prefixes on a 1-page doc
        return pages
    if n == 2:
        prefix_threshold = 1.0
    else:  # n >= 3
        prefix_threshold = 1 / 3 + 0.01
    prefix_counts = {}
    for page in pages:
        for i in range(MIN_PREFIX_LENGTH, len(page)):
            if top:
                prefix = page[:i]
            else:
                # go from the bottom of the page
                # technically this is a suffix, but whatever
                prefix = page[-i:]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    # if no discovered prefixes
    new_pages = pages.copy()
    for prefix in sorted(prefix_counts.keys(), key=lambda x: -1 * len(x)):
        if prefix_counts[prefix] / n >= prefix_threshold:
            for page in new_pages:
                new_pages = [page.replace(prefix, "\n") for page in new_pages]
            for i in range(MIN_PREFIX_LENGTH, len(prefix)):
                if top:
                    prefix_counts[prefix[:i]] -= prefix_counts[prefix]
                else:
                    prefix_counts[prefix[-i:]] -= prefix_counts[prefix]
    return new_pages


def remove_sub_and_superscripts(pages):
    new_pages = []
    for page in pages:
        new_pages.append(re.sub(r"(\D[a-zA-z\.“”`'\",]+)(\d+)(\s)", r"\1\3", page))
    return new_pages


def remove_numeric_citations(pages):
    # remove inline numerical-only citations, e.g. [1], [6-7]
    new_pages = []
    for page in pages:
        new_pages.append(
            re.sub(r"\[\d+(\-\d+)?(,\s?\d+(\-\d+)?)+\]", "(citation)", page)
        )
    return new_pages


def remove_footnotes(pages):
    new_pages = []
    MAX_FOOTNOTES = 10000
    footnote_iter = iter(range(MAX_FOOTNOTES))
    for page in pages:
        new_page = ""
        # TODO do stuff
        new_pages.append(new_page)
    return new_pages


# TODO remove the sequence of increasing bulleted items.
# Given previous bullet was x, each bullet begins with \n[whitespace]x+1[whitespace][. or )]
# and ends with the next bullet, or the end of the page.
# Also remember to delete the reference in the text itself.
# (For this reason, when searching, best to start from the bottom to not run into the text reference accidentally)


def place_footnotes_inline(pages, prefix="Foonote: "):
    raise NotImplementedError()


# TODO Same as above, except instead of deletion, place it in the text at the location where previously the reference number occurred


def extract_ints(s):
    if isinstance(s, str):
        return [int(c) for c in s.split() if c.isdigit()]
    else:
        return [extract_ints(elt) for elt in s]


def remove_trailing_blank_pages(pages):
    for i, page in reversed(list(enumerate(pages))):
        if not page.isspace() and page:
            # page isn't empty and has something other than whitspace
            break
    return pages[: (i + 1)]


# TODO remove figures/tables
