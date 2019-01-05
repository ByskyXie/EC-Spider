import sys
import time
import hashlib
import logging
import pymysql
import selenium
import traceback
import exception
import mitmproxy.http
from entity import Item
from entity import Commodity
from selenium import webdriver
from selenium.webdriver.common.by import By


class Launcher:

    def __init__(self) -> None:
        super().__init__()

    """
        method: 
            The EC-Spider's entrance. you could selected scratch TaoBao/Tmall or jd.
    """
    def launch_spider(self, browser: selenium.webdriver.Chrome, **ec_list):
        # TODO:初始化
        self.chrome_option_initial(browser)

    '''
        method: 
            hide selenium features and then pass the spider detection.
        param: 
            browser is an instance of browser which includes Chrome/Edge/FireFox etc.
    '''
    @staticmethod
    def anti_detected_initial(browser: selenium.webdriver.Chrome):
        browser.execute_script("""
            if (navigator.webdriver) {
                navigator.webdrivser = false;
                delete navigator.webdrivser;
                Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
            }""")

    """
        method: 
            Before launch spider, set chrome option to accelerate the speed.
        param:
            chrome: Instance of selenium.webdriver.Chrome.
    """
    def chrome_option_initial(self, chrome: selenium.webdriver.Chrome):
        # TODO:无图模式
        options = webdriver.ChromeOptions()  # chrome设置
        options.add_argument("disable-cache")

    def access_taobao(self, browser: selenium.webdriver.Chrome):
        # 淘宝
        browser.get('http://www.taobao.com')
        input = browser.find_element(By.ID, 'q')
        input.send_keys('U盘')
        button = browser.find_element(By.CLASS_NAME, 'search-button').find_element(By.TAG_NAME, 'button')
        if button is None:
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
        if button is None:
            print('Get button failed')
        else:
            button.click()

    def get_commodity_type_list(self):
        pass


class JdDetailPageReader:
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_detail_page_specification_xpath = "//*[@class=\'summary p-choose-wrap\']/*"
    __jd_detail_page_color_xpath = "//*[@id=\'choose-attr-1\']/*"  # jd颜色选项
    __jd_detail_page_edition_xpath = "//*[@id=\'choose-attr-2\']/*"  # jd版本选项
    __jd_detail_page_price_xpath = "//span[@class=\'p-price\']/span[@*]"  # 价格
    __jd_detail_page_plus_price_xpath = "//span[@class=\'p-price-plus\']/span[@*]"  # plus会员价
    __jd_detail_page_ticket_xpath = "//div[@id=\'summary-quan\']//span[@class=\'quan-item\']"  # 优惠券
    __jd_detail_page_remark_xpath = "//li[contains(text(),\'商品评价\')]/*"  # 商品评价
    __jd_detail_page_item_name_xpath = "//div[@class=\'sku-name\']"  # 商品名称
    __jd_detail_page_item_type_xpath = "//div[@class=\'crumb fl clearfix\']"  # 商品类别
    __jd_detail_page_store_name_xpath = "//div[@class=\'contact fr clearfix\']//div[@class=\'name\']/a"  # 店铺名

    def __init__(self) -> None:
        super().__init__()

    """
        method: 
            Rely the supplied jd commodity detail page. the method format read in info and then return a 
            commodity instance.
        param: 
            browser: an instance of browser which includes Chrome/Edge/FireFox etc. 
            cautiously, the browser current page must be a commodity page.
    """
    def get_jd_commodity_from_detail_page(self, browser: selenium.webdriver.Chrome) -> Commodity:
        # TODO:判断是否是详情页，且有可能长时间未响应/无货/链接无效
        comm = Commodity()
        # 获取商品url
        comm.item_url = browser.current_url
        # 获取商品title
        comm.item_title = browser.title
        # 获取商品name
        comm.item_name = self.get_jd_item_name_from_detail_page(browser)
        # 获取商品分类
        comm.item_type = self.get_jd_item_type_from_detail_page(browser)
        # 获取店铺url
        comm.store_url = self.get_jd_store_url_from_detail_page(browser)
        # 获取店铺名
        comm.store_name = self.get_jd_store_name_from_detail_page(browser)
        return comm

    """
        method: 
            Rely the supplied jd item detail page. the method format read in info and then return a 
            item instance.
        param: 
            browser: an instance of browser which includes Chrome/Edge/FireFox etc. 
            cautiously, the browser current page must be a commodity detail page.
    """
    def get_jd_item_from_detail_page(self, browser: selenium.webdriver.Chrome) -> Item:
        # TODO:判断是否是详情页，且有可能长时间未响应/无货/链接无效
        item = Item()
        # 获取颜色标题及所选项目值
        color_dom = self.get_jd_color_dom_from_detail_page(browser)
        if color_dom is not None and len(color_dom) != 0:
            color_title_str = color_dom[0].text  # 获取标题
            color_selected_str = color_dom[1].find_element(By.CLASS_NAME, "selected").text  # 获取已选值
            item.spec1 = color_title_str + '=' + color_selected_str
        else:
            # 某些单一款不需要选颜色
            pass
        # 获取版本标题及所选项目值
        edition_dom = self.get_jd_edition_dom_from_detail_page(browser)
        if edition_dom is not None and len(edition_dom) != 0:
            edition_title_str = edition_dom[0].text
            edition_selected_str = edition_dom[1].find_element(By.CLASS_NAME, "selected").text
            item.spec2 = edition_title_str + '=' + edition_selected_str
        else:
            # 说明不需要选择型号，或者说没有型号信息
            pass
        # 获取价格
        item.price = self.get_jd_price_from_detail_page(browser)
        # 获取plus会员价格
        item.plus_price = self.get_jd_plus_price_from_detail_page(browser)
        # 获取商品url
        item.url = browser.current_url
        # 领券
        ticket_dom = self.get_jd_ticket_dom_from_detail_page(browser)
        if ticket_dom is not None and len(ticket_dom) != 0:
            ticket_str = ''
            for ti in ticket_dom:
                ticket_str += ti.text + '\n'
            item.ticket = ticket_str
        # 库存:京东不显示库存量，只有有无货之分
        # 快递费:京东各省价格均不同，有货情况也不同故不做记录
        # 销量
        item.sales_amount = self.get_jd_remark_from_detail_page(browser)
        # 可选字段
        # 生成所有字段
        item.generate_all_specification()
        return item

    def get_jd_store_name_from_detail_page(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_store_name_xpath).text.strip()

    def get_jd_store_url_from_detail_page(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_store_name_xpath).get_attribute('href')

    def get_jd_item_name_from_detail_page(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_item_name_xpath).text.strip()

    def get_jd_item_type_from_detail_page(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_item_type_xpath).text.strip()

    def get_jd_specification_dom_from_detail_page(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_specification_xpath)

    def get_jd_color_dom_from_detail_page(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_color_xpath)

    def get_jd_edition_dom_from_detail_page(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_edition_xpath)

    def get_jd_ticket_dom_from_detail_page(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_ticket_xpath)

    def get_jd_remark_from_detail_page(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_remark_xpath).text[1: -2]

    def get_jd_price_from_detail_page(self, browser: selenium.webdriver.Chrome) -> float:
        try:
            return float(browser.find_element(By.XPATH, self.__jd_detail_page_price_xpath).text)
        except ValueError:
            return -1

    def get_jd_plus_price_from_detail_page(self, browser: selenium.webdriver.Chrome) -> float:
        try:
            return float(browser.find_element(By.XPATH, self.__jd_detail_page_plus_price_xpath).text[1:])
        except ValueError:
            return -1


class DatabaseHelper:
    # TODO:数据库结构有更新，相关操作需要更改！
    __sql_insert_item = "INSERT INTO ITEM(item_url_md5,item_url,data_date,item_price," \
                        "plus_price, ticket, inventory, sales_amount, transport_fare," \
                        "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
                        "VALUE ('%s','%s',%f,%f,%f,'%s',%d,'%s',%f" \
                        ",'%s','%s','%s','%s','%s','%s','%s');"
    __sql_insert_commodity = "INSERT INTO COMMODITY(item_url_md5,item_url, item_title," \
                             "item_name, item_type, store_name, store_url) " \
                             "VALUE ('%s','%s','%s','%s','%s','%s','%s');"
    __sql_query_commodity = "SELECT * FROM commodity WHERE item_url_md5='%s';"
    __sql_query_item = "SELECT * FROM item WHERE item_url_md5='%s' and data_date=%f;"

    __connection = None

    def __init__(self):
        __connection = self.__get_mysql_connection()

    def __del__(self):
        if self.__connection is not None and self.__is_mysql_connect_valid(self.__connection):
            self.__connection.close()  # 关闭连接

    """
        仅供类内部使用，不能开放接口给外界读取，防止恶意关闭连接！
        DO NOT use the method in outside, it could lead to unexpected ERROR!
        method:
            return a member connection of mysql, it confirm are alive.
    """
    def __get_mysql_connection(self) -> pymysql.connections.Connection:
        if self.__connection is None:
            # TODO:从外部文件读入用户名及密码！
            self.__connection = pymysql.connect(
                user='root', password='mysql233', charset='utf8',
                database='ec_spider', use_unicode=True
            )
        # 防止之前关闭，重新连接
        self.__connection.ping(True)
        return self.__connection

    """
        method: 
            detect whether the supplied mysql connection alive.
    """
    @staticmethod
    def __is_mysql_connect_valid(connect: pymysql.connections.Connection) -> bool:
        try:
            connect.ping(False)
        except pymysql.err.Error:
            return False
        return True

    """
        method: 
            save gave commodity info into mysql database.
        param: 
            commodity: instance of Commodity, you must be confirm commodity.item_url not None.
    """
    def insert_commodity(self, commodity: Commodity):
        if type(commodity) != Commodity:
            return
        # 检查是否存在,是的话跳过
        if self.is_commodity_exist(commodity.item_url_md5):
            logging.info('Url_md5:', commodity.item_url_md5, ' existed in database.')
            return
        cursor = self.__connection.cursor()
        try:
            cursor.execute(self.__sql_insert_commodity % (
                commodity.item_url_md5, commodity.item_url, commodity.item_title, commodity.item_name,
                commodity.item_type, commodity.store_name, commodity.store_url
            ))
            self.__connection.commit()
        except Exception:
            traceback.print_exc()
            raise
        finally:
            cursor.close()

    """
        method: 
            save gave item info into mysql database.
        param: 
            item: instance of Item, you must be confirm item.item_url and item.data_date not None.
    """
    def insert_item(self, item: Item):
        if type(item) != Item:
            return
        if self.is_item_exist(item):
            logging.info('Url_md5:', item.item_url_md5, ' Data_date:', item.data_date, ' existed in database.')
            return
        cursor = self.__connection.cursor()
        try:
            cursor.execute(self.__sql_insert_item % (
                item.item_url_md5, item.url, item.data_date, item.price, item.plus_price, item.ticket,
                item.inventory, item.sales_amount, item.transport_fare, item.all_specification,
                item.spec1, item.spec2, item.spec3, item.spec4, item.spec5, item.spec_other
            ))
            self.__connection.commit()
        except Exception:
            traceback.print_exc()
            raise
        finally:
            cursor.close()

    def is_commodity_exist(self, commodity_md5: str) -> bool:
        if self.__connection.query(self.__sql_query_commodity % (commodity_md5,)) > 0:
            return True
        return False

    def is_item_exist(self, item: Item) -> bool:
        if self.__connection.query(self.__sql_query_item % (item.item_url_md5, item.data_date)) > 0:
            return True
        return False



if __name__ == '__main__':
    laun = Launcher()
    helper = DatabaseHelper()
    jddr = JdDetailPageReader()
    # ############# 当初的少年怎么也不会想到
    chrome = webdriver.Chrome()
    chrome.get('https://item.jd.com/8735304.html#none')
    comm = jddr.get_jd_commodity_from_detail_page(chrome)
    item = jddr.get_jd_item_from_detail_page(chrome)
    helper.insert_commodity(comm)
    helper.insert_item(item)
    time.sleep(10)
    chrome.close()

# https://item.jd.com/8735304.html#none
# http://item.jd.com/20742438990.html # 只有商品颜色选择
# http://item.jd.com/28252543502.html # 优惠券
# https://item.jd.com/35165938134.html # plus
