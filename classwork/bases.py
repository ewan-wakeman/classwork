import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)
from collections.abc import KeysView, ItemsView, ValuesView
from inspect import isclass, ismethod
from datetime import date
from enum import Enum
from logzero import logger

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


class ParamsBase(ClassworkABC):
    """A default ParamBase"""

    def __init__(
        self,
        params: Mapping[str, Any] = {},
        ignore_check: bool = False,
        **kwargs,
    ):
        """ """
        super().__init__(params=params, ignore_check=ignore_check, **kwargs)


class MultiIndexDict(ClassWorkBase):

    indexes: List[str]
    collection: Tuple[Any, ...]

    def __repr__(self):

        index = {idx: self[idx] for idx in self.indexes}
        itype = {type(itm) for itm in self.collection}
        coll = {
            _: len([itm for itm in self.collection if type(itm) is _]) for _ in itype
        }

        return f"<{self.__class__}> {index} - {coll}"

    def match(self, *, ignore_missing: bool = True, **keys) -> bool:

        keys_present = [key for key in keys if key in self.indexes]
        keys_missing = [key for key in keys if key not in self.indexes]
        if len(keys_missing) > 0 and (not ignore_missing):
            raise KeyError(f"Keys {keys_missing} not present in {self}")

        return all([self.keymatch(keys[x], self[x]) for x in keys_present])

    @staticmethod
    def keymatch(key_x, key_y) -> bool:
        scalars = (str, date, int, float, Enum)
        ranges = (range, slice)
        # return True if either are None
        if key_x is None or key_y is None:
            return True
        # if both scalars try to match
        elif isinstance(key_x, scalars) & isinstance(key_y, scalars):
            return key_x == key_y
        # if one is a slice check the key is in the range
        elif isinstance(key_x, ranges) | isinstance(key_y, ranges):
            if isinstance(key_y, ranges):
                return (key_x >= key_y.start) & (key_x < key_y.stop)
            else:
                return (key_y >= key_x.start) & (key_y < key_x.stop)
        # if one of the two is a scalar (and one is not)
        # check for presence of scalar in iterable (if poss)
        elif isinstance(key_x, scalars) ^ isinstance(key_y, scalars):
            if isinstance(key_x, scalars):
                if isinstance(key_y, Sequence):
                    return key_x in key_y
                elif isinstance(key_y, dict):
                    return key_x in key_y.values()
                else:
                    return False
            else:
                if isinstance(key_x, Sequence):
                    return key_y in key_x
                elif isinstance(key_x, dict):
                    return key_y in key_x.values()
                else:
                    return False
        # if both sets are sequences check for valid intersection
        elif isinstance(key_x, Sequence) & isinstance(key_y, Sequence):
            if set(key_x) & set(key_y):
                return True
            else:
                return False
        # Other methods not implemented warn and leave
        else:
            logger.warning(
                f"Unsure what to to with pairs of type {type(key_x)} & {type(key_y)}"
            )
            return False


_Child = TypeVar("_Child", bound=ClassworkMeta)
_Type = TypeVar("_Type")


class ParamSet(MultiIndexDict):

    scen_keys: Optional[List[str]] = None
    geo_keys: Optional[List[str]] = None
    date_key: Optional[date] = None

    indexes: List[str] = ["scen_keys", "geo_keys", "date_key"]
    collection: Tuple[ClassWorkBase, ...]

    def __init__(
        self,
        params: Dict[str, List] = {},
        collection: Iterable[ClassWorkBase] = [],
        *,
        scen_keys: Optional[List[str]] = None,
        geo_keys: Optional[List[str]] = None,
        date_key: Optional[date] = None,
        **kwargs,
    ):
        arg_keys = {
            "scen_keys": scen_keys,
            "geo_keys": geo_keys,
            "date_key": date_key,
        }
        kwargs.update({k: v for k, v in arg_keys.items() if v})

        super().__init__(params, collection=collection, **kwargs)
        self.collection = self._check_collection(collection)

    @classmethod
    def _check_collection(
        cls, collection: Iterable[ClassWorkBase], child: ClassworkMeta = ClassWorkBase
    ) -> Tuple[ClassWorkBase, ...]:

        tup: Tuple[ClassWorkBase, ...] = ()
        if isinstance(collection, Sequence):
            tup = tuple(itm for itm in collection)
            assert all(isinstance(itm, child) for itm in tup), (
                f"Expected sequence of {child} but recieved items of type "
                f"{set(type(x) for x in collection)}."
            )
        elif isinstance(collection, Mapping):
            tup = tuple(itm for itm in collection.values())
            assert all(isinstance(itm, child) for itm in tup), (
                f"Expected sequence of {child} but recieved items of type "
                f"{set(type(x) for x in collection)}."
            )
        elif isinstance(collection, child):
            tup = tuple(collection)
        else:
            raise TypeError(
                f"Expected sequence of {child} but recieved item of type "
                f"{type(collection)}."
            )

        return tup
