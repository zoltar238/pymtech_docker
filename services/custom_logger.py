import logging


class CustomLogFormatter(logging.Formatter):
    """Formatter that adds styling to logs """

    # Color definitions using ANSI escape sequences
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    # Formatos para cada nivel
    FORMATS = {
        logging.DEBUG: f"{CYAN}%(message)s{RESET}",
        logging.INFO: f"{BLUE}[STATUS] %(message)s{RESET}",
        logging.WARNING: f"{YELLOW}[WARNING] %(message)s{RESET}",
        logging.ERROR: f"{RED}[ERROR] %(message)s{RESET}",
        logging.CRITICAL: f"{RED}[CRITICAL] %(message)s{RESET}",
        # Success level
        25: f"{GREEN}[SUCCESS] %(message)s{RESET}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomLogger(logging.Logger):
    """Logger that uses the custom formatter"""


    def __init__(self, name: str):
        super().__init__(name)
        self.name = name

        # Add success level to logs
        logging.addLevelName(25, "SUCCESS")

        log_level = logging.DEBUG

        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomLogFormatter())
        console_handler.setLevel(log_level)

        self.logger.addHandler(console_handler)

    def print_header(self, message):
        """Print header"""
        self.logger.debug("=" * 60)
        self.logger.debug(message)
        self.logger.debug("=" * 60)

    def print_status(self, message):
        """Print info messages"""
        self.logger.info(message)

    def print_error(self, message):
        """Print error messages"""
        self.logger.error(message)

    def print_warning(self, message):
        """Print warning messages."""
        self.logger.warning(message)

    def print_critical(self, message):
        """Print critical messages."""
        self.logger.critical(message)

    def print_success(self, message):
        """Print success messages."""
        self.logger.log(25, message)
