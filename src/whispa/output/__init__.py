"""Text output and injection module."""

from whispa.output.injector import TextInjector
from whispa.output.clipboard import ClipboardInjector
from whispa.output.keyboard import KeyboardInjector

__all__ = ["TextInjector", "ClipboardInjector", "KeyboardInjector"]
