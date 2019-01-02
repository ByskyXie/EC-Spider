import sys
import selenium
import mitmproxy.http
from selenium import webdriver
from selenium.webdriver.common.by import By


class Launcher:
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_specification_xpath = "//*[@class=\'summary p-choose-wrap\']/*"

    def __init__(self):
        pass

    def launch_spider(self):
        pass

    '''
        function: hide selenium features and then pass the spider detection.
        param: browser is an instance of browser which includes Chrome/Edge/FireFox etc.
    '''
    def anti_detected_initial(self, browser: selenium.webdriver.Chrome):
        browser.execute_script("""
            if (navigator.webdriver) {
                navigator.webdrivser = false;
                delete navigator.webdrivser;
                Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
            }""")

    def get_jd_specification(self, browser: selenium.webdriver.Chrome):
        dom = self.get_jd_specification_dom(browser)
        for item in dom:
            if item.is_displayed():
                # 隐藏属性不处理
                continue
            # 获取div id判断是否与保存字段相符，若无记录则直接保存
            class_name = item.get_attribute('id')

    def get_jd_specification_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_specification_xpath)

    def access_taobao(self, browser: selenium.webdriver.Chrome):
        # 淘宝
        browser.get('http://www.taobao.com')
        input = browser.find_element(By.ID, 'q')
        input.send_keys('U盘')
        button = browser.find_element(By.CLASS_NAME, 'search-button').find_element(By.TAG_NAME, 'button')
        if (button is None):
            print('Get button failed')
        else:
            button.click()

    def access_jd(self, browser: selenium.webdriver.Chrome):
        # 京东
        chrome.get('http://www.jd.com')
        input = chrome.find_element(By.ID, 'key')
        input.send_keys('U盘')
        button = chrome.find_element(By.XPATH, '//*[@class=\'search-m\']').find_element(By.CLASS_NAME, 'button')
        chrome.execute_script("""   
            if (navigator.webdriver) {
                navigator.webdrivser = false;
                delete navigator.webdrivser;
                Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
            }""")  # 检测无头模式，为真则做出修改
        if (button is None):
            print('Get button failed')
        else:
            button.click()


if __name__ == '__main__':
    options = webdriver.ChromeOptions()  # chrome设置
    options.add_argument("disable-cache")
    ##############
    chrome = webdriver.Chrome()
    chrome.get('https://item.jd.com/8735304.html#')
    dom = Launcher().get_jd_specification_dom(chrome)
    if dom is not None:
        print('DOM ', type(dom), ' content:\n')
        for item in dom:
            print(item.text, end='\n...............\n')
        print('\n===============\n')
    else:
        print('Empty dom')
