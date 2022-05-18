import logging


def pytest_configure(config):
    """Disable noisy upstream loggers."""
    # From https://stackoverflow.com/a/57002853/2160256
    disabled_loggers = {"pdfminer"}
    for name in disabled_loggers:
        logger = logging.getLogger(name)
        logger.setLevel("WARN")
