import time
from typing import Any


class Item:
    __item_url = ''
    __item_price = 0
    __plus_price = 0
    __ticket = ''
    __inventory = 0
    __data_date = time.time()
    __sales_amount = 0
    __transport_fare = 0
    __all_specification = ''
    __spec1 = None
    __spec2 = None
    __spec3 = None
    __spec4 = None
    __spec5 = None
    __spec_other = None

    def __init__(self):
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    def get_str_time(self):
        time_array = time.localtime(self.__data_date)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
