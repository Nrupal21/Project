"""
Template tags for the reviews app.

This package contains custom template tags and filters for the reviews app.
To use these in templates, add `{% load review_filters %}` at the top of your template.
"""

# Import the template tag modules to ensure they are registered
from . import review_filters  # noqa
from . import content_type_tags  # noqa

# This file makes the directory a Python package
# The imports above ensure that the template tags are registered when Django starts

# Import the template tags to ensure they're registered
from .review_filters import *  # noqa