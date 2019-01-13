from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class PageViewsAppear:

    def __init__(self, element_list: list):
        self.element_list = element_list

    def __call__(self, driver):
        for element in self.element_list:
            if not EC.presence_of_all_elements_located(element):
                return False
        return True


