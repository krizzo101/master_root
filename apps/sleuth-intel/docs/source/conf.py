"""
Sphinx configuration for Sleuth Intel API Documentation
"""

import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath("../../"))
sys.path.insert(0, os.path.abspath("../../src"))

# Project information
project = "Sleuth Intel"
copyright = f"{datetime.now().year}, Sleuth Intel Development Team"
author = "Sleuth Intel Development Team"
release = "1.0.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.ifconfig",
    "sphinx_rtd_theme",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "myst_parser",
    "sphinxcontrib.mermaid",
    "autodoc_pydantic",
]

# Extension settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False

# Napoleon settings for Google style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# MyST parser for Markdown support
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_admonition",
    "html_image",
    "colon_fence",
    "smartquotes",
    "replacements",
    "linkify",
    "substitution",
]

# Intersphinx mappings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "pydantic": ("https://docs.pydantic.dev/", None),
}

# Templates path
templates_path = ["_templates"]

# Exclude patterns
exclude_patterns = []

# HTML theme settings
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}

# HTML static files
html_static_path = ["_static"]

# HTML extras
html_favicon = None
html_logo = None
html_show_sourcelink = True
html_show_sphinx = False
html_show_copyright = True

# Output file base name
html_title = f"{project} Documentation"
html_short_title = project

# LaTeX output settings
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "htbp",
}

# Grouping the document tree
latex_documents = [
    ("index", "sleuth_intel.tex", f"{project} Documentation", author, "manual"),
]

# Manual page output
man_pages = [("index", "sleuth_intel", f"{project} Documentation", [author], 1)]

# Texinfo output
texinfo_documents = [
    (
        "index",
        "sleuth_intel",
        f"{project} Documentation",
        author,
        "sleuth_intel",
        "Advanced OSINT Investigation Framework",
        "Miscellaneous",
    ),
]

# Copy button configuration
copybutton_prompt_text = r">>> |\\$ |In \\[\\d*\\]: | {2,5}\\.\\.\\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Todo extension settings
todo_include_todos = True
