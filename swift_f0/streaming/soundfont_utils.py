"""
SoundFont discovery and management utilities.

Provides automatic SoundFont detection in common locations to simplify user experience.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def find_soundfonts(search_dirs: Optional[List[str]] = None) -> List[Path]:
    """
    Discover available SoundFont files in common locations.

    Args:
        search_dirs: Optional list of directories to search.
                    If None, uses default locations.

    Returns:
        List of Path objects to .sf2/.sf3 files, sorted by size (largest first)

    Default search locations:
        1. ./soundfonts/ (project directory)
        2. ~/Audio/SoundFonts/
        3. /usr/share/soundfonts/ (Linux)
        4. /usr/local/share/soundfonts/ (macOS Homebrew)

    Example:
        >>> soundfonts = find_soundfonts()
        >>> if soundfonts:
        ...     print(f"Found: {soundfonts[0]}")
    """
    if search_dirs is None:
        # Default search locations
        project_root = Path(__file__).parent.parent.parent
        search_dirs = [
            str(project_root / "soundfonts"),  # Project soundfonts dir
            os.path.expanduser("~/Audio/SoundFonts"),  # User audio dir
            os.path.expanduser("~/.soundfonts"),  # Hidden user dir
            "/usr/share/soundfonts",  # System (Linux)
            "/usr/local/share/soundfonts",  # Homebrew (macOS)
        ]

    found: List[Path] = []

    for dir_path in search_dirs:
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            continue

        # Search for .sf2 and .sf3 files
        for ext in ["*.sf2", "*.sf3"]:
            found.extend(p.glob(ext))

    # Sort by size (largest first, usually better quality)
    found.sort(key=lambda x: x.stat().st_size, reverse=True)

    return found


def get_default_soundfont() -> Optional[Path]:
    """
    Get the default SoundFont to use (largest available).

    Returns:
        Path to SoundFont file, or None if none found

    Example:
        >>> sf = get_default_soundfont()
        >>> if sf:
        ...     config = AudioSynthConfig(soundfont_path=str(sf), ...)
    """
    soundfonts = find_soundfonts()
    return soundfonts[0] if soundfonts else None


def format_soundfont_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "31.2 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def list_available_soundfonts() -> None:
    """
    Print available SoundFonts to console (for CLI tools).

    Example output:
        Found 2 SoundFont(s):
          1. GeneralUser-GS.sf2 (31.2 MB) - soundfonts/GeneralUser-GS.sf2
          2. MuseScore_General.sf3 (35.1 MB) - ~/Audio/SoundFonts/MuseScore_General.sf3
    """
    soundfonts = find_soundfonts()

    if not soundfonts:
        print("No SoundFonts found. Please download one:")
        print("  - GeneralUser GS: http://www.schristiancollins.com/generaluser.php")
        print("  - FluidR3 GM: https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.tar.gz")
        print("\nPlace in: ./soundfonts/ or ~/Audio/SoundFonts/")
        return

    print(f"Found {len(soundfonts)} SoundFont(s):")
    for i, sf_path in enumerate(soundfonts, 1):
        size = format_soundfont_size(sf_path.stat().st_size)
        print(f"  {i}. {sf_path.name} ({size}) - {sf_path}")


def resolve_soundfont_path(path_or_auto: str) -> str:
    """
    Resolve SoundFont path (supports 'auto' keyword for automatic discovery).

    Args:
        path_or_auto: File path or 'auto' for automatic discovery

    Returns:
        Resolved absolute path to SoundFont file

    Raises:
        FileNotFoundError: If path not found or no SoundFonts discovered

    Example:
        >>> # Explicit path
        >>> path = resolve_soundfont_path("soundfonts/GeneralUser-GS.sf2")
        >>> # Automatic discovery
        >>> path = resolve_soundfont_path("auto")
    """
    if path_or_auto.lower() == "auto":
        sf = get_default_soundfont()
        if sf is None:
            raise FileNotFoundError(
                "No SoundFonts found in default locations. Please download one:\n"
                "  1. GeneralUser GS: http://www.schristiancollins.com/generaluser.php\n"
                "  2. FluidR3 GM: https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.tar.gz\n"
                "\n"
                "Place in: ./soundfonts/ or ~/Audio/SoundFonts/"
            )
        return str(sf.resolve())

    # Explicit path
    p = Path(path_or_auto)
    if not p.exists():
        raise FileNotFoundError(f"SoundFont not found: {path_or_auto}")

    return str(p.resolve())
