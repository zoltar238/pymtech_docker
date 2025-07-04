# Color definitions using ANSI escape sequences
class Colors:
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def print_header(message):
    print()
    print(f"{Colors.BOLD}{Colors.BLUE}================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE} {message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}================================{Colors.RESET}")


def print_status(message):
    print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")


def print_error(message):
    print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")


def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING] {message}{Colors.RESET}")


def print_success(message):
    print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.RESET}")