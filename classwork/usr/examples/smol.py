from logzero import logger
from abc import ABCMeta, abstractmethod


class SmolMeta(ABCMeta):
    def __call__(cls, **kw):
        logger.info(f"{cls.__name__}.__call__")
        logger.info(f"kwargs: {kw}")
        if "_cls" in kw:
            _cls = kw.pop("_cls")
            logger.info(f"subclassing to {_cls.__name__}")
            inst = _cls(**kw)
        else:
            inst = object.__new__(cls)
            inst.__init__(**kw)
        return inst


class SmolAbc(metaclass=SmolMeta):
    @abstractmethod
    def something(self):
        logger.info("something")


class SmolMum(SmolAbc):
    def __new__(cls, **kw):
        logger.info(f"{cls.__name__}.__new__")

    def something(self):
        super().something()


class SmolBeb(SmolMum):
    def __init__(self, **kw):
        logger.info(f"{self.__class__.__name__}.__init__ with {kw}")
        params = kw
        params.update(kw)

        for k, v in params.items():
            setattr(self, k, v)


if __name__ == "__main__":
    sm = SmolMum(_cls=SmolBeb, name="hello")
    logger.info(sm.__dict__)
