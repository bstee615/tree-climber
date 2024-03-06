import abc


class BaseParser(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def parse(data, *args, **kwargs):
        pass
