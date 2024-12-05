class Colors:
    HEADER = '\033[95m'
    WARNING = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @staticmethod
    def color_text(text: str, *color_codes: str) -> str:
        color_code = ''.join(color_codes)
        return f'{color_code}{text}{Colors.RESET}'
