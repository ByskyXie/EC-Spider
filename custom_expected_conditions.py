import launcher
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class PageViewsAppear:

    def __init__(self, element_list: list):
        self.element_list = element_list

    def __call__(self, driver):
        for element in self.element_list:
            if not EC.presence_of_all_elements_located(element).__call__(driver):
                return False
        return True


class ResultAllAppear:

    def __init__(self) -> None:
        pass

    def __call__(self, driver: webdriver.Chrome):
        ele_list = driver.find_elements(By.XPATH, launcher.JdListPageReader.jd_list_page_goods_list_xpath)
        if launcher.JdListPageReader.jd_list_page_goods_list_amount == len(ele_list):
            return True
        return False



