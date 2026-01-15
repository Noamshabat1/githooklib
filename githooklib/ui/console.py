from typing import Optional
import sys
import platform

from ..logger import get_logger

logger = get_logger()

_global_console: Optional["Console"] = None

# Platform-specific symbols (Windows can't always handle Unicode emojis)
IS_WINDOWS = platform.system() == "Windows"
SYMBOLS = {
    "success": "[OK]" if IS_WINDOWS else "✓",
    "error": "[X]" if IS_WINDOWS else "✗",
    "warning": "[!]" if IS_WINDOWS else "⚠",
    "info": "[i]" if IS_WINDOWS else "ℹ",
}


class Console:
    def __init__(self, use_colors: bool = True, use_rich: bool = True) -> None:
        self.use_colors = use_colors
        self.use_rich = use_rich
        self._rich_console = None
        
        if use_rich:
            try:
                from rich.console import Console as RichConsole
                self._rich_console = RichConsole()
                logger.trace("Rich console initialized")
            except ImportError:
                logger.trace("Rich not available, falling back to colorama")
                self.use_rich = False
        
        if use_colors and not use_rich:
            try:
                import colorama
                colorama.init(autoreset=True)
                logger.trace("Colorama initialized")
            except ImportError:
                logger.trace("Colorama not available, colors disabled")
                self.use_colors = False
    
    def print(self, message: str, style: Optional[str] = None) -> None:
        if self._rich_console and self.use_rich:
            if style:
                self._rich_console.print(message, style=style)
            else:
                self._rich_console.print(message)
        elif self.use_colors and style:
            print(self._apply_color(message, style))
        else:
            print(message)
    
    def print_success(self, message: str) -> None:
        symbol = SYMBOLS["success"]
        if self._rich_console:
            self._rich_console.print(f"{symbol} {message}", style="bold green")
        elif self.use_colors:
            try:
                from colorama import Fore, Style
                print(f"{Fore.GREEN}{symbol} {message}{Style.RESET_ALL}")
            except ImportError:
                print(f"{symbol} {message}")
        else:
            print(f"{symbol} {message}")
    
    def print_error(self, message: str) -> None:
        symbol = SYMBOLS["error"]
        if self._rich_console:
            self._rich_console.print(f"{symbol} {message}", style="bold red")
        elif self.use_colors:
            try:
                from colorama import Fore, Style
                print(f"{Fore.RED}{symbol} {message}{Style.RESET_ALL}", file=sys.stderr)
            except ImportError:
                print(f"{symbol} {message}", file=sys.stderr)
        else:
            print(f"{symbol} {message}", file=sys.stderr)
    
    def print_warning(self, message: str) -> None:
        symbol = SYMBOLS["warning"]
        if self._rich_console:
            self._rich_console.print(f"{symbol} {message}", style="bold yellow")
        elif self.use_colors:
            try:
                from colorama import Fore, Style
                print(f"{Fore.YELLOW}{symbol} {message}{Style.RESET_ALL}")
            except ImportError:
                print(f"{symbol} {message}")
        else:
            print(f"{symbol} {message}")
    
    def print_info(self, message: str) -> None:
        symbol = SYMBOLS["info"]
        if self._rich_console:
            self._rich_console.print(f"{symbol} {message}", style="bold blue")
        elif self.use_colors:
            try:
                from colorama import Fore, Style
                print(f"{Fore.BLUE}{symbol} {message}{Style.RESET_ALL}")
            except ImportError:
                print(f"{symbol} {message}")
        else:
            print(f"{symbol} {message}")
    
    def print_table(self, headers: list[str], rows: list[list[str]]) -> None:
        if self._rich_console:
            try:
                from rich.table import Table
                table = Table()
                for header in headers:
                    table.add_column(header, style="cyan")
                for row in rows:
                    table.add_row(*row)
                self._rich_console.print(table)
                return
            except ImportError:
                pass
        
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        header_line = "  ".join(
            header.ljust(width) for header, width in zip(headers, col_widths)
        )
        separator = "  ".join("-" * width for width in col_widths)
        
        print(header_line)
        print(separator)
        
        for row in rows:
            row_line = "  ".join(
                str(cell).ljust(width) for cell, width in zip(row, col_widths)
            )
            print(row_line)
    
    def _apply_color(self, message: str, style: str) -> str:
        try:
            from colorama import Fore, Style as ColorStyle
            
            color_map = {
                "green": Fore.GREEN,
                "red": Fore.RED,
                "yellow": Fore.YELLOW,
                "blue": Fore.BLUE,
                "cyan": Fore.CYAN,
                "magenta": Fore.MAGENTA,
            }
            
            color = color_map.get(style, "")
            if color:
                return f"{color}{message}{ColorStyle.RESET_ALL}"
        except ImportError:
            pass
        
        return message
    
    def progress_bar(self, total: int, desc: str = "Progress"):
        if self._rich_console:
            try:
                from rich.progress import Progress
                return Progress()
            except ImportError:
                pass
        
        try:
            from tqdm import tqdm
            return tqdm(total=total, desc=desc)
        except ImportError:
            return None


def get_console() -> Console:
    global _global_console
    
    if _global_console is None:
        _global_console = Console()
    
    return _global_console


__all__ = ["Console", "get_console"]

