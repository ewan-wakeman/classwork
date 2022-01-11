import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar
from collections.abc import KeysView, ItemsView, ValuesView
from inspect import isclass, ismethod
from .meta import ClassworkABC, ClassworkMeta, DefaultAbc, PathLike
from .codecs import ClassworkEncoder, ClassworkDecoder


ClassworkBaseType = TypeVar("ClassworkBaseType", bound="ClassWorkBase")


class ClassWorkBase(ClassworkABC):

    encoder = ClassworkEncoder
    decoder = ClassworkDecoder

    def __init__(self, params: Mapping[str, Any] = {}, **kwargs):
        default_attrs: List[str] = [
            attr
            for attr in self.__class__.__dict__
            if not any(
                [ismethod(self[attr]), isclass(self[attr]), attr.startswith("_")]
            )
        ]
        self._default_attrs = default_attrs
        super().__init__(params=params, **kwargs)

    def __getitem__(self, attr: str) -> Any:
        return super().__getitem__(attr)

    def __setitem__(self, attr: str, value: Any) -> None:
        if attr not in self._default_attrs:
            attr = f"_{attr}"
        return super().__setitem__(attr, value)

    def __iter__(self):
        for k in self._default_attrs:
            yield k

    def __repr__(self):
        if len(list(self)) > 5:
            head = list(self)[:4]
            tail = list(self)[-1]
            disp_keys = [head] + [...] + [tail]
        else:
            disp_keys = list(self)

        return " ".join((str(self.__class__), str(disp_keys)))

    def items(self, defaults: bool = False, hidden: bool = False) -> ItemsView:
        dct = self.asdict(defaults, hidden)
        return dct.items()

    def values(self, defaults: bool = False, hidden: bool = False) -> ValuesView:
        dct = self.asdict(defaults, hidden)
        return dct.values()

    def keys(self, defaults: bool = False, hidden: bool = False) -> KeysView:
        dct = self.asdict(defaults, hidden)
        return dct.keys()

    def asdict(self, defaults: bool = False, hidden: bool = False) -> Dict[str, Any]:
        dct = {}
        if defaults:
            dct.update(
                {
                    k: v
                    for k, v in self.__class__.__dict__.items()
                    if not k.startswith("__")
                }
            )

        dct.update(self.__dict__)

        if not hidden:
            dct = {k: v for k, v in dct.items() if not k.startswith("_")}

        return dct

    def update(self, params: Mapping[str, Any] = {}, **kwargs) -> None:
        return super().update(params=params, **kwargs)

    def _class_dict(
        self, defaults: bool = False, hidden: bool = False
    ) -> Dict[str, Any]:

        dct = self.asdict(defaults, hidden)
        _cls = self.__class__.__name__
        o: Dict[str, Any] = {"_cls": _cls, "_params": dct}

        return o

    def to_json_str(
        self, defaults: bool = False, hidden: bool = False, **kwargs
    ) -> str:
        """Returns the object encoded as a json string."""

        o = self._class_dict(defaults, hidden)
        json_str = json.dumps(o, cls=self.encoder, **kwargs)

        return json_str

    def to_json_file(
        self, path: PathLike, defaults: bool = False, hidden: bool = False, **kwargs
    ) -> Path:

        if isinstance(path, str):
            path = Path(path)

        o = self._class_dict(defaults, hidden)
        json.dump(o, path.open("w"), cls=self.encoder, **kwargs)

        return path

    @classmethod
    def from_json(
        cls: Type[ClassworkBaseType],
        path: Optional[PathLike] = None,
        json_str: Optional[str] = None,
    ) -> ClassworkBaseType:
        o: Dict = {}
        if path:
            if not isinstance(path, Path):
                path = Path(path)

            o.update(json.load(path.open("r"), cls=cls.decoder))

        elif json_str:

            o.update(json.loads(json_str, cls=cls.decoder))

        else:

            raise AttributeError(
                f"{cls.__name__}.from_json() requires one of path or json_str"
            )

        return cls(o)


class DefaultDecorator(DefaultAbc):
    """
    DefaultDecorator

    Typical Usage
    ```
    @DefaultDecorator({"a":5, "b": "hello"})
    class NewClass():
        a: int
        b: str
    ```
    """

    def __init__(self, params: Dict[str, Any] = {}, **kwargs):
        """
        Takes key value pairs in the form of a `params` dict or `**kwargs` and
        assigns them to a new instance of this class. This can then be
        """
        super().__init__(params=params, **kwargs)

    def __call__(self, cls: ClassworkMeta) -> ClassworkMeta:
        """
        Assigns any items in self.defaults as default attrs on the class
        provided to the cls argument. This is automatically called when
        an initialised instance of this class is used as a decorator for
        another class.
        """
        return super().__call__(cls)
