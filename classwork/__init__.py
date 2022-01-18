from . import classes
from .meta import ClassworkMeta

cls_dct = {
    f"{cls.__module__}.{cls.__name__}": cls
    for cls in classes.__dict__.values()
    if isinstance(cls, ClassworkMeta)
}
