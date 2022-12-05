from .cli import main
from .utils import version

__version__ = version()
__all__ = ["__version__", "main"]
