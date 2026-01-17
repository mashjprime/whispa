"""Voice command detection and execution."""

import re
import logging
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)


class CommandAction(Enum):
    """Types of voice command actions."""

    INSERT_TEXT = auto()
    CONTROL = auto()


@dataclass
class VoiceCommand:
    """Definition of a voice command."""

    triggers: list[str]
    action: CommandAction
    value: str
    description: str


class VoiceCommandProcessor:
    """Processes voice commands in transcribed text."""

    # Default voice commands
    DEFAULT_COMMANDS = [
        # Punctuation
        VoiceCommand(["period", "full stop"], CommandAction.INSERT_TEXT, ".", "Insert period"),
        VoiceCommand(["comma"], CommandAction.INSERT_TEXT, ",", "Insert comma"),
        VoiceCommand(
            ["question mark"], CommandAction.INSERT_TEXT, "?", "Insert question mark"
        ),
        VoiceCommand(
            ["exclamation mark", "exclamation point"],
            CommandAction.INSERT_TEXT,
            "!",
            "Insert exclamation mark",
        ),
        VoiceCommand(["colon"], CommandAction.INSERT_TEXT, ":", "Insert colon"),
        VoiceCommand(["semicolon"], CommandAction.INSERT_TEXT, ";", "Insert semicolon"),
        VoiceCommand(
            ["open quote", "open quotes", "begin quote"],
            CommandAction.INSERT_TEXT,
            '"',
            "Open quotes",
        ),
        VoiceCommand(
            ["close quote", "close quotes", "end quote"],
            CommandAction.INSERT_TEXT,
            '"',
            "Close quotes",
        ),
        VoiceCommand(
            ["open parenthesis", "open paren", "left paren"],
            CommandAction.INSERT_TEXT,
            "(",
            "Open parenthesis",
        ),
        VoiceCommand(
            ["close parenthesis", "close paren", "right paren"],
            CommandAction.INSERT_TEXT,
            ")",
            "Close parenthesis",
        ),
        VoiceCommand(["hyphen", "dash"], CommandAction.INSERT_TEXT, "-", "Insert hyphen"),
        VoiceCommand(
            ["ellipsis", "dot dot dot"], CommandAction.INSERT_TEXT, "...", "Insert ellipsis"
        ),
        # Whitespace
        VoiceCommand(
            ["new line", "newline", "next line"],
            CommandAction.INSERT_TEXT,
            "\n",
            "Insert new line",
        ),
        VoiceCommand(
            ["new paragraph", "next paragraph"],
            CommandAction.INSERT_TEXT,
            "\n\n",
            "Insert new paragraph",
        ),
        VoiceCommand(["tab"], CommandAction.INSERT_TEXT, "\t", "Insert tab"),
        # Special
        VoiceCommand(
            ["no space"], CommandAction.CONTROL, "no_space", "Remove trailing space"
        ),
    ]

    def __init__(self, enabled: bool = True, commands: list[VoiceCommand] = None):
        """Initialize voice command processor.

        Args:
            enabled: Whether command processing is enabled
            commands: Custom commands (uses defaults if None)
        """
        self.enabled = enabled
        self._commands = commands or self.DEFAULT_COMMANDS.copy()
        self._pattern = self._build_pattern()

    def _build_pattern(self) -> re.Pattern:
        """Build regex pattern for command matching."""
        all_triggers = []
        for cmd in self._commands:
            all_triggers.extend(cmd.triggers)

        # Sort by length (longest first)
        all_triggers.sort(key=len, reverse=True)

        # Escape and join
        escaped = [re.escape(t) for t in all_triggers]
        pattern = r"\b(" + "|".join(escaped) + r")\b"

        return re.compile(pattern, re.IGNORECASE)

    def process(self, text: str) -> Tuple[str, bool]:
        """Process voice commands in text.

        Args:
            text: Input text

        Returns:
            Tuple of (processed_text, had_commands)
        """
        if not self.enabled or not text:
            return text, False

        had_commands = False
        result = text

        # Find all command matches
        for cmd in self._commands:
            for trigger in cmd.triggers:
                pattern = re.compile(r"\b" + re.escape(trigger) + r"\b", re.IGNORECASE)

                if pattern.search(result):
                    had_commands = True

                    if cmd.action == CommandAction.INSERT_TEXT:
                        # Replace trigger with value
                        result = pattern.sub(cmd.value, result)
                    elif cmd.action == CommandAction.CONTROL:
                        # Handle control commands
                        result = pattern.sub("", result)
                        if cmd.value == "no_space":
                            result = result.rstrip()

        # Clean up whitespace around inserted punctuation
        if had_commands:
            result = self._clean_punctuation_spacing(result)

        return result, had_commands

    def _clean_punctuation_spacing(self, text: str) -> str:
        """Clean up spacing around punctuation after command insertion."""
        # Remove space before punctuation
        text = re.sub(r"\s+([.,!?;:)\]])", r"\1", text)

        # Remove space after opening brackets
        text = re.sub(r"([([\[])\s+", r"\1", text)

        # Ensure space after closing punctuation followed by letter
        text = re.sub(r"([.,!?;:)\]])\s*([A-Za-z])", r"\1 \2", text)

        # Clean multiple spaces
        text = re.sub(r" +", " ", text)

        return text.strip()

    def add_command(self, command: VoiceCommand) -> None:
        """Add a custom command.

        Args:
            command: Command to add
        """
        self._commands.append(command)
        self._pattern = self._build_pattern()

    def remove_command(self, trigger: str) -> bool:
        """Remove a command by trigger.

        Args:
            trigger: Any trigger of the command to remove

        Returns:
            True if removed
        """
        trigger_lower = trigger.lower()
        for i, cmd in enumerate(self._commands):
            if trigger_lower in [t.lower() for t in cmd.triggers]:
                del self._commands[i]
                self._pattern = self._build_pattern()
                return True
        return False

    def get_commands(self) -> list[VoiceCommand]:
        """Get all registered commands."""
        return self._commands.copy()
