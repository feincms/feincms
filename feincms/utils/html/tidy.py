# encoding: utf-8

"""Utilities for dealing with HTML content"""


import re

import tidylib

# Based on http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
#
# We omit chars 9-13 (tab, newline, vertical tab, form feed, return) and 32
# (space) to avoid clogging our reports with warnings about common,
# non-problematic codes but still allow stripping things which will cause lxml
# to choke

CONTROL_CHAR_RE = re.compile('[%s]' % "".join(
    re.escape(unichr(c)) for c in range(0, 8) + range(14, 31) + range(127, 160)
))


def tidy_html(html):
    """
    Process an input string containing HTML and return a tuple (xhtml,
    errors, warnings) containing the output of tidylib and lists of
    validation errors and warnings.

    Input must be unicode.
    Output will be valid XHTML.
    """
    if not isinstance(html, unicode):
        raise ValueError("tidyhtml must be called with a Unicode string!")

    warnings = list()

    # First, deal with embedded control codes:
    html, sub_count = CONTROL_CHAR_RE.subn(" ", html)
    if sub_count:
        warnings.append("Stripped %d control characters from body: %s" % (
            sub_count,
            set(ord(i) for i in CONTROL_CHAR_RE.findall(html))
        ))

    # tidylib.tidy_fragment will choke if given a full HTML document. This is a
    # primitive content sniff to decide whether to call tidy_document instead:
    if "<html" in html[:1024]:
        tidy_f = tidylib.tidy_document
        doc_mode = True
    else:
        tidy_f = tidylib.tidy_fragment
        doc_mode = False

    html, messages = tidy_f(
        html.strip(),
        {
            "char-encoding":               "utf8",
            "clean":                        False,
            "drop-empty-paras":             False,
            "drop-font-tags":               True,
            "drop-proprietary-attributes":  False,
            "fix-backslash":                True,
            "indent":                       True,
            "output-xhtml":                 True,
        }
    )

    messages = filter(None, (l.strip() for l in messages.split("\n") if l))

    # postprocess warnings to avoid HTML fragments being reported as lacking
    # doctype and title:
    errors = list()
    warnings = list()

    for msg in messages:
        if not doc_mode and "Warning: missing <!DOCTYPE> declaration" in msg:
            continue
        if not doc_mode and "Warning: inserting missing 'title' element" in msg:
            continue
        if not doc_mode and "Warning: inserting implicit <body>" in msg:
            continue

        if "Error:" in msg:
            errors.append(msg)
        else:
            warnings.append(msg)

    return html, errors, warnings
