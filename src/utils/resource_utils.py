"""Utility functions for handling resources in the project."""
from pathlib import Path


def get_resource_path(filename: str) -> str:
    """
    Get the absolute path to a file in the resources directory.

    Args:
        filename (str): Name of the file in the resources directory

    Returns:
        str: Absolute path to the resource file
    """
    # Get the absolute path to the resources directory
    resources_dir = Path(__file__).parent.parent / "resources"
    return str(resources_dir / filename)
