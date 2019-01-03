import sys
import selenium
import time
from item import Item
import exception
import mitmproxy.http
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


class Launcher:
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_specification_xpath = "//*[@class=\'summary p-choose-wrap\']/*"
    __jd_color_xpath = "//*[@id=\'choose-attr-1\']/*"  # jd颜色选项
    __jd_edition_xpath = "//*[@id=\'choose-attr-2\']/*"  # jd版本选项
    __jd_price_xpath = "//span[@class=\'p-price\']/span[@*]"  # 价格
    __jd_plus_price_xpath = "//span[@class=\'p-price-plus\']/span[@*]"  # plus会员价
    __jd_ticket_xpath = "//div[@id=\'summary-quan\']//span[@class=\'quan-item\']"  # 优惠券
    __jd_remark_xpath = "//li[contains(text(),\'商品评价\')]/*"  # 商品评价

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
        item = Item()
        # 获取颜色标题及所选项目值
        color_dom = self.get_jd_color_dom(browser)
        if color_dom is not None and len(color_dom) != 0:
            color_title_str = color_dom[0].text  # 获取标题
            color_selected_str = color_dom[1].find_element(By.CLASS_NAME, "selected").text  # 获取已选值
        else:
            # 某些单一款不需要选颜色
            pass
        # 获取版本标题及所选项目值
        edition_dom = self.get_jd_edition_dom(browser)
        if edition_dom is not None and len(edition_dom) != 0:
            edition_title_str = edition_dom[0].text
            edition_selected_str = edition_dom[1].find_element(By.CLASS_NAME, "selected").text
        else:
            # 说明不需要选择型号，或者说没有型号信息
            pass
        # 获取价格
        price = self.get_jd_price(browser)
        # 获取plus会员价格
        plus_price = self.get_jd_plus_price(browser)
        # 获取商品url
        url = browser.current_url
        # 领券
        ticket_dom = self.get_jd_ticket_dom(browser)
        if ticket_dom is not None and len(ticket_dom) != 0:
            # TODO:add to data
            pass
        # 库存:京东不显示库存量，只有有无货之分
        # 销量
        sales = self.get_jd_remark(browser)
        print(sales)
        # 快递费:京东各省价格均不同，有货情况也不同故不做记录
        # 可选字段
        # 获取div id判断是否与保存字段相符，若无记录则直接保存，有可能未响应

    def get_jd_specification_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_specification_xpath)

    def get_jd_color_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_color_xpath)

    def get_jd_edition_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_edition_xpath)

    def get_jd_ticket_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_ticket_xpath)

    def get_jd_remark(self, browser: selenium.webdriver.Chrome):
        return browser.find_element(By.XPATH, self.__jd_remark_xpath).text[1: -2]

    def get_jd_price(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_price_xpath).text

    def get_jd_plus_price(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_plus_price_xpath).text[1:]

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
        browser.get('http://www.jd.com')
        input = browser.find_element(By.ID, 'key')
        input.send_keys('U盘')
        button = browser.find_element(By.XPATH, '//*[@class=\'search-m\']').find_element(By.CLASS_NAME, 'button')
        browser.execute_script("""   
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
    chrome.get('http://item.jd.com/28252543502.html#none')
    laun = Launcher()
    laun.get_jd_specification(chrome)
    time.sleep(10)
    chrome.close()

# http://item.jd.com/20742438990.html # 只有商品颜色选择
# http://item.jd.com/28252543502.html # 优惠券
