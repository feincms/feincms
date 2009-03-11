from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class RSSContent(models.Model):
	link = models.URLField(_('link'))

	class Meta:
		abstract = True

	def render(self, **kwargs):
		return mark_safe(u'<div class="rsscontent"> RSS: <a href="'+self.link+'">'+self.link+'</a></div')

