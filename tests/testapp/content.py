from django.db import models


class CustomContentType(models.Model):
    class Meta:
        abstract = True
