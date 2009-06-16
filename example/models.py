from feincms.module.page.models import Page
from feincms.content.raw.models import RawContent
from feincms.content.image.models import ImageContent

Page.create_content_type(RawContent)
Page.create_content_type(ImageContent)
