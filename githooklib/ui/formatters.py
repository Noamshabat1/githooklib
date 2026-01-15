from typing import List


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    header_line = "  ".join(
        header.ljust(width) for header, width in zip(headers, col_widths)
    )
    separator = "  ".join("-" * width for width in col_widths)
    
    lines = [header_line, separator]
    
    for row in rows:
        row_line = "  ".join(
            str(cell).ljust(width) for cell, width in zip(row, col_widths)
        )
        lines.append(row_line)
    
    return "\n".join(lines)


def format_success(message: str) -> str:
    return f"✓ {message}"


def format_error(message: str) -> str:
    return f"✗ {message}"


def format_warning(message: str) -> str:
    return f"⚠ {message}"


def format_info(message: str) -> str:
    return f"ℹ {message}"


__all__ = [
    "format_table",
    "format_success",
    "format_error",
    "format_warning",
    "format_info",
]

