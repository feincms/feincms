from feincms.module.page.models import Page
from feincms.content.raw.models import RawContent
from feincms.content.image.models import ImageContent

Page.register_templates({
    'key': 'base',
    'title': 'Base Template',
    'path': 'base.html',
    'regions': (
        ('main', 'Main region'),
        ('sidebar', 'Sidebar', 'inherited'),
        ),
    })
Page.create_content_type(RawContent)
Page.create_content_type(ImageContent)
