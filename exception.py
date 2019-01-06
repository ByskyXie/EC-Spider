from types import TracebackType
from typing import Optional, Any


class SpecNotFoundException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def with_traceback(self, tb: Optional[TracebackType]) -> BaseException:
        return super().with_traceback(tb)

    def __str__(self) -> str:
        return 'Commodity specification find failed, maybe should check xpath or something!\n' + super().__str__()

    def __new__(cls) -> Any:
        return super().__new__(cls)



class GetUrlFailedException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)