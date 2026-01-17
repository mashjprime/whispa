"""Tests for text processing module."""

import pytest

from whispa.text_processing.filler_words import FillerWordRemover
from whispa.text_processing.commands import VoiceCommandProcessor, CommandAction
from whispa.text_processing.formatting import TextFormatter
from whispa.text_processing.snippets import SnippetExpander, Snippet
from whispa.text_processing.dictionary import DictionaryCorrector, DictionaryEntry


class TestFillerWordRemover:
    """Tests for FillerWordRemover."""

    def test_remove_basic_fillers(self):
        """Test removal of basic filler words."""
        remover = FillerWordRemover()

        text = "Um, I think, like, this is actually a good idea"
        result = remover.remove(text)

        assert "um" not in result.lower()
        assert "like" not in result.lower()
        assert "actually" not in result.lower()
        assert "good idea" in result.lower()

    def test_remove_phrase_fillers(self):
        """Test removal of phrase fillers."""
        remover = FillerWordRemover(filler_words=["you know", "i mean"])

        text = "You know, I mean, it's really important"
        result = remover.remove(text)

        assert "you know" not in result.lower()
        assert "i mean" not in result.lower()
        assert "really important" in result.lower()

    def test_disabled_remover(self):
        """Test disabled remover returns original text."""
        remover = FillerWordRemover(enabled=False)

        text = "Um, this is a test"
        result = remover.remove(text)

        assert result == text

    def test_empty_text(self):
        """Test empty text handling."""
        remover = FillerWordRemover()

        assert remover.remove("") == ""
        assert remover.remove(None) is None

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        remover = FillerWordRemover(filler_words=["um"])

        assert "um" not in remover.remove("UM test").lower()
        assert "um" not in remover.remove("Um test").lower()
        assert "um" not in remover.remove("um test").lower()


class TestVoiceCommandProcessor:
    """Tests for VoiceCommandProcessor."""

    def test_period_command(self):
        """Test period insertion."""
        processor = VoiceCommandProcessor()

        text, had_commands = processor.process("Hello world period")

        assert "." in text
        assert "period" not in text.lower()
        assert had_commands is True

    def test_multiple_commands(self):
        """Test multiple commands in one text."""
        processor = VoiceCommandProcessor()

        text, _ = processor.process("Hello comma world period")

        assert "," in text
        assert "." in text
        assert "comma" not in text.lower()
        assert "period" not in text.lower()

    def test_new_line_command(self):
        """Test new line insertion."""
        processor = VoiceCommandProcessor()

        text, _ = processor.process("Line one new line Line two")

        assert "\n" in text
        assert "new line" not in text.lower()

    def test_new_paragraph_command(self):
        """Test new paragraph insertion."""
        processor = VoiceCommandProcessor()

        text, _ = processor.process("Paragraph one new paragraph Paragraph two")

        assert "\n\n" in text

    def test_disabled_processor(self):
        """Test disabled processor returns original text."""
        processor = VoiceCommandProcessor(enabled=False)

        text, had_commands = processor.process("Hello period")

        assert text == "Hello period"
        assert had_commands is False

    def test_no_commands(self):
        """Test text without commands."""
        processor = VoiceCommandProcessor()

        text, had_commands = processor.process("Hello world")

        assert text == "Hello world"
        assert had_commands is False


class TestTextFormatter:
    """Tests for TextFormatter."""

    def test_auto_capitalize_first(self):
        """Test first letter capitalization."""
        formatter = TextFormatter(auto_capitalize=True)

        result = formatter.format("hello world")

        assert result.startswith("H")

    def test_auto_capitalize_after_period(self):
        """Test capitalization after period."""
        formatter = TextFormatter(auto_capitalize=True)

        result = formatter.format("hello. world")

        assert "Hello" in result
        assert ". W" in result or ". w" not in result

    def test_clean_whitespace(self):
        """Test whitespace cleanup."""
        formatter = TextFormatter()

        result = formatter.format("hello    world")

        assert "    " not in result
        assert "hello world" in result.lower()

    def test_fix_punctuation_spacing(self):
        """Test punctuation spacing."""
        formatter = TextFormatter()

        result = formatter.format("hello , world")

        assert " ," not in result
        assert "hello," in result.lower()

    def test_append_to_existing(self):
        """Test intelligent text appending."""
        formatter = TextFormatter()

        # Normal append
        result = formatter.append_to_existing("Hello", "world")
        assert result == "Hello world"

        # Append punctuation
        result = formatter.append_to_existing("Hello", ".")
        assert result == "Hello."

        # Existing trailing space
        result = formatter.append_to_existing("Hello ", "world")
        assert result == "Hello world"


class TestSnippetExpander:
    """Tests for SnippetExpander."""

    def test_expand_snippet(self):
        """Test basic snippet expansion."""
        expander = SnippetExpander()
        expander.load_snippets([
            Snippet(id=1, trigger="myemail", expansion="user@example.com",
                   category="", description=""),
        ])

        text, expanded = expander.expand("Send to myemail please")

        assert "user@example.com" in text
        assert "myemail" not in text
        assert expanded is True

    def test_multiple_snippets(self):
        """Test multiple snippet expansions."""
        expander = SnippetExpander()
        expander.load_snippets([
            Snippet(id=1, trigger="myemail", expansion="user@example.com",
                   category="", description=""),
            Snippet(id=2, trigger="myphone", expansion="555-1234",
                   category="", description=""),
        ])

        text, _ = expander.expand("Contact: myemail or myphone")

        assert "user@example.com" in text
        assert "555-1234" in text

    def test_no_expansion(self):
        """Test text without snippets."""
        expander = SnippetExpander()
        expander.load_snippets([
            Snippet(id=1, trigger="myemail", expansion="user@example.com",
                   category="", description=""),
        ])

        text, expanded = expander.expand("Hello world")

        assert text == "Hello world"
        assert expanded is False

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        expander = SnippetExpander()
        expander.load_snippets([
            Snippet(id=1, trigger="myemail", expansion="user@example.com",
                   category="", description=""),
        ])

        text, _ = expander.expand("Send to MYEMAIL")
        assert "user@example.com" in text


class TestDictionaryCorrector:
    """Tests for DictionaryCorrector."""

    def test_basic_correction(self):
        """Test basic word correction."""
        corrector = DictionaryCorrector()
        corrector.load_entries([
            DictionaryEntry(id=1, original="teh", replacement="the",
                           case_sensitive=False, whole_word=True),
        ])

        text, count = corrector.correct("teh quick brown fox")

        assert "the quick" in text
        assert "teh" not in text
        assert count == 1

    def test_case_preservation(self):
        """Test case preservation in corrections."""
        corrector = DictionaryCorrector()
        corrector.load_entries([
            DictionaryEntry(id=1, original="api", replacement="API",
                           case_sensitive=False, whole_word=True),
        ])

        # Should preserve original case
        text, _ = corrector.correct("the api is ready")
        assert "API" in text

    def test_whole_word_only(self):
        """Test whole word matching."""
        corrector = DictionaryCorrector()
        corrector.load_entries([
            DictionaryEntry(id=1, original="the", replacement="THE",
                           case_sensitive=False, whole_word=True),
        ])

        text, count = corrector.correct("the other thing")

        assert text.startswith("THE ")
        # "other" should not be affected
        assert "oTHEr" not in text

    def test_case_sensitive(self):
        """Test case sensitive matching."""
        corrector = DictionaryCorrector()
        corrector.load_entries([
            DictionaryEntry(id=1, original="API", replacement="Application Programming Interface",
                           case_sensitive=True, whole_word=True),
        ])

        text1, count1 = corrector.correct("The API is ready")
        text2, count2 = corrector.correct("The api is ready")

        assert "Application Programming Interface" in text1
        assert count1 == 1
        assert "api" in text2.lower()
        assert count2 == 0
