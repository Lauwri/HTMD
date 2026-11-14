"""HTMD 0.1/0.2 parser and non-executing runtime components."""
from .parser import HTMDError, Document, Parser, parse, parse_file
from .render import render_html
from .resolver import Registry
__all__ = ["HTMDError", "Document", "Parser", "parse", "parse_file", "render_html", "Registry"]
__version__ = "0.2.0a1"
