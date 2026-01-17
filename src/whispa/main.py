"""Main entry point for Whispa application."""

import sys
import logging
from pathlib import Path

from whispa.config.paths import get_app_paths
from whispa.utils.logging import setup_logging
from whispa.utils.single_instance import SingleInstanceLock


def main() -> int:
    """Main entry point."""
    # Setup paths
    paths = get_app_paths()
    paths.ensure_directories()

    # Setup logging
    setup_logging(paths.log_file)
    logger = logging.getLogger(__name__)
    logger.info("Starting Whispa...")

    # Check single instance
    lock = SingleInstanceLock("whispa-voice-dictation")
    if not lock.acquire():
        logger.warning("Another instance of Whispa is already running")
        return 1

    try:
        # Import Qt app here to avoid loading it if another instance is running
        from whispa.ui.app import WhispaApplication

        app = WhispaApplication(sys.argv)
        return app.run()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        return 1
    finally:
        lock.release()
        logger.info("Whispa stopped")


if __name__ == "__main__":
    sys.exit(main())
