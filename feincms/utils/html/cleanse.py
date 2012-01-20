from BeautifulSoup import BeautifulSoup
import lxml.html
import lxml.html.clean
import re
import unicodedata


cleanse_html_allowed = {
    'a': ('href', 'name', 'target', 'title'),
    'h2': (),
    'h3': (),
    'strong': (),
    'em': (),
    'p': (),
    'ul': (),
    'ol': (),
    'li': (),
    'span': (),
    'br': (),
    'sub': (),
    'sup': (),
    'anything': (),
    }

cleanse_html_allowed_empty_tags = ('br',)

cleanse_html_merge = ('h2', 'h3', 'strong', 'em', 'ul', 'ol', 'sub', 'sup')


def cleanse_html(html):
    """
    Clean HTML code from ugly copy-pasted CSS and empty elements

    Removes everything not explicitly allowed in ``cleanse_html_allowed``.

    Requires ``lxml`` and ``beautifulsoup``.
    """

    doc = lxml.html.fromstring('<anything>%s</anything>' % html)
    try:
        ignore = lxml.html.tostring(doc, encoding=unicode)
    except UnicodeDecodeError:
        # fall back to slower BeautifulSoup if parsing failed
        from lxml.html import soupparser
        doc = soupparser.fromstring(u'<anything>%s</anything>' % html)

    cleaner = lxml.html.clean.Cleaner(
        allow_tags=cleanse_html_allowed.keys() + ['style'],
        remove_unknown_tags=False, # preserve surrounding 'anything' tag
        style=False, safe_attrs_only=False, # do not strip out style
                                            # attributes; we still need
                                            # the style information to
                                            # convert spans into em/strong
                                            # tags
        )

    cleaner(doc)

    # walk the tree recursively, because we want to be able to remove
    # previously emptied elements completely
    for element in reversed(list(doc.iterdescendants())):
        if element.tag == 'style':
            element.drop_tree()
            continue

        # convert span elements into em/strong if a matching style rule
        # has been found. strong has precedence, strong & em at the same
        # time is not supported
        elif element.tag == 'span':
            style = element.attrib.get('style')
            if style:
                if 'bold' in style:
                    element.tag = 'strong'
                elif 'italic' in style:
                    element.tag = 'em'

            if element.tag == 'span': # still span
                element.drop_tag() # remove tag, but preserve children and text
                continue

        # remove empty tags if they are not <br />
        elif not element.text and element.tag not in \
                cleanse_html_allowed_empty_tags and not \
                len(list(element.iterdescendants())):
            element.drop_tag()
            continue

        # remove all attributes which are not explicitly allowed
        allowed = cleanse_html_allowed.get(element.tag, [])
        for key in element.attrib.keys():
            if key not in allowed:
                del element.attrib[key]

    # just to be sure, run cleaner again, but this time with even more
    # strict settings
    cleaner = lxml.html.clean.Cleaner(
        allow_tags=cleanse_html_allowed.keys(),
        remove_unknown_tags=False, # preserve surrounding 'anything' tag
        style=True, safe_attrs_only=True
        )

    cleaner(doc)

    html = lxml.html.tostring(doc, method='xml')

    # remove all sorts of newline characters
    html = html.replace('\n', ' ').replace('\r', ' ')
    html = html.replace('&#10;', ' ').replace('&#13;', ' ')
    html = html.replace('&#xa;', ' ').replace('&#xd;', ' ')

    # remove wrapping tag needed by XML parser
    html = re.sub(r'</?anything>', '', html)

    # remove elements containing only whitespace or linebreaks
    whitespace_re = re.compile(r'<([a-z0-9]+)>(<br\s*/>|\&nbsp;|\&#160;|\s)*</\1>')
    while True:
        new = whitespace_re.sub('', html)
        if new == html:
            break
        html = new

    # merge tags
    for tag in cleanse_html_merge:
        merge_str = u'</%s><%s>'
        while True:
            new = html.replace(merge_str, u'')
            if new == html:
                break
            html = new

    # fix p-in-p tags
    p_in_p_start_re = re.compile(r'<p>(\&nbsp;|\&#160;|\s)*<p>')
    p_in_p_end_re = re.compile('</p>(\&nbsp;|\&#160;|\s)*</p>')

    for tag in cleanse_html_merge:
        merge_start_re = re.compile('<p>(\\&nbsp;|\\&#160;|\\s)*<%s>(\\&nbsp;|\\&#160;|\\s)*<p>' % tag)
        merge_end_re = re.compile('</p>(\\&nbsp;|\\&#160;|\\s)*</%s>(\\&nbsp;|\\&#160;|\\s)*</p>' % tag)

        while True:
            new = merge_start_re.sub('<p>', html)
            new = merge_end_re.sub('</p>', new)
            new = p_in_p_start_re.sub('<p>', new)
            new = p_in_p_end_re.sub('</p>', new)

            if new == html:
                break
            html = new

    # remove list markers with <li> tags before them
    html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*(-|\*|&#183;)(\&nbsp;|\&#160;|\s)*', '<li>', html)

    # remove p-in-li tags
    html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*<p>', '<li>', html)
    html = re.sub(r'</p>(\&nbsp;|\&#160;|\s)*</li>', '</li>', html)

    # add a space before the closing slash in empty tags
    html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

    # nicify entities and normalize unicode
    html = unicode(BeautifulSoup(html, convertEntities='xml'))
    html = unicodedata.normalize('NFKC', html)

    return html

