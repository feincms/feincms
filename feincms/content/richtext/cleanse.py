import lxml.html
import lxml.html.clean
import re


cleanse_html_allowed = {
    'a': ('href', 'target', 'title'),
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

    Removes everything not explicitly allowed in `cleanse_html_allowed`
    above.
    """

    doc = lxml.html.fromstring('<anything>%s</anything>' % html)
    try:
        ignore = lxml.html.tostring(doc, encoding=unicode)
    except UnicodeDecodeError:
        # fall back to slower BeautifulSoup if parsing failed
        from lxml.html import soupparser
        doc = soupparser.fromstring(u'<anything>%s</anything>' % html)

    cleaner = lxml.html.clean.Cleaner(
        allow_tags=cleanse_html_allowed.keys(),
        remove_unknown_tags=False, # preserve surrounding 'anything' tag
        style=False, safe_attrs_only=False, # do not strip out style
                                            # attributes; we still need
                                            # the style information to
                                            # convert spans into em/strong
                                            # tags
        )
    doc = cleaner.clean_html(doc)

    for element in reversed(list(doc.iterdescendants())):
        # convert span elements into em/strong if a matching style rule
        # has been found. strong has precedence, strong & em at the same
        # time is not supported
        if element.tag == 'span':
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

    html = lxml.html.tostring(doc, method='xml')

    # remove all sorts of newline characters
    html = html.replace('\n', '').replace('\r', '')
    html = html.replace('&#10;', '').replace('&#13;', '')
    html = html.replace('&#xa;', '').replace('&#xd;', '')

    # remove wrapping tag needed by XML parser
    html = re.sub(r'</?anything>', '', html)

    # remove elements containing only whitespace or linebreaks
    whitespace_re = re.compile(r'<([a-z]+)>(<br\s*/>|\&nbsp;|\&#160;|\s)*</\1>')
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
    p_in_p_start_str = '<p><p>'
    p_in_p_end_str = '</p></p>'

    for tag in cleanse_html_merge:
        merge_start_str = '<p><%s><p>' % tag
        merge_end_str = '</p></%s></p>' % tag

        while True:
            new = html.replace(merge_start_str, '<p>')
            new = new.replace(merge_end_str, '</p>')
            new = new.replace(p_in_p_start_str, '<p>')
            new = new.replace(p_in_p_end_str, '</p>')

            if new == html:
                break
            html = new

    # remove list markers with <li> tags before them
    html = re.sub(r'<li>\s*(-|\*)\s*', '<li>', html)

    # add a space before the closing slash in empty tags
    html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

    return html

