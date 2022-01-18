from .usr import classes
from .meta import ClassworkMeta

__all__ = [
    cls.__name__ for cls in classes.__dict__.values() if isinstance(cls, ClassworkMeta)
]
