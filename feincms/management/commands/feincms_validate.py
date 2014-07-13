# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``feincms_validate``
--------------------

``feincms_validate`` checks your models for common pitfalls.
"""
from __future__ import absolute_import, unicode_literals

from django.core.management.base import NoArgsCommand
from django.core.management.color import color_style
from django.db.models import loading


class Command(NoArgsCommand):
    help = "Check models for common pitfalls."

    requires_model_validation = False

    def handle_noargs(self, **options):
        self.style = color_style()

        self.stdout.write("Running Django's own validation:")
        self.validate(display_num_errors=True)

        for model in loading.get_models():
            if hasattr(model, '_create_content_base'):
                self.validate_base_model(model)

            if hasattr(model, '_feincms_content_models'):
                self.validate_content_type(model)

    def validate_base_model(self, model):
        """
        Validate a subclass of ``feincms.models.Base`` or anything else
        created by ``feincms.models.create_base_model``
        """

        if not hasattr(model, 'template'):
            self.stdout.write(self.style.NOTICE(
                '%s has no template attribute; did you forget'
                ' register_templates or register_regions?' % model))

    def validate_content_type(self, model):
        """
        Validate a dynamically created concrete content type
        """

        for base in model.__bases__:
            if not base._meta.abstract:
                self.stdout.write(self.style.NOTICE(
                    'One of %s bases, %s, is not abstract' % (model, base)))
