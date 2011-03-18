from django.core.management.color import color_style

style = color_style()

print style.ERROR("""This module (%s) is experimental. Use at your own risk.""" % __name__)
