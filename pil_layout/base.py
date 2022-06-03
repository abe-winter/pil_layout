import abc, inspect
from .units import Dim

NO_SOURCES = False # so asserts don't have to find the layout object in test suite

class Layout(abc.ABC):
    "ultimate base class"

    def source(self):
        return None if NO_SOURCES else self

    @staticmethod
    def stack():
        "parse the stack to create a 'stack trace' of our depth in the layout tree"
        classes = []
        for frame in inspect.stack():
            if frame.frame.f_code.co_name == 'compute':
                _, _, _, value_dict = inspect.getargvalues(frame.frame)
                if (frame_self := value_dict.get('self')):
                    if issubclass(frame_self.__class__, Layout):
                        classes.append(frame_self.__class__.__name__)
        return list(reversed(classes))

    @abc.abstractmethod
    def compute(self, dim: Dim, dpi: int):
        ...
