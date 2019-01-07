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
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement


class Launcher:

    def __init__(self) -> None:
        super().__init__()

    def launch_spider(self, browser: selenium.webdriver.Chrome, **ec_list):
        """
        method:
            The EC-Spider's entrance. you could selected scratch TaoBao/Tmall or jd.
        :param browser:
        :param ec_list:
        :return:
        """
        # TODO:初始化
        with webdriver.Chrome(self.chrome_option_initial()) as chrome:
            pass

    @staticmethod
    def anti_detected_initial(browser: selenium.webdriver.Chrome):
        """
        method:
            hide selenium features and then pass the spider detection.
        :param
            browser is an instance of browser which includes Chrome/Edge/FireFox etc.
        :return:
        """
        with open('anti_detect_strategy.js', 'r') as strategy:
            str_script = strategy.readline()
            while True:
                i = strategy.readline()
                if len(i) == 0:
                    break
                str_script += i
        browser.execute_script(str_script)

    @staticmethod
    def chrome_option_initial() -> webdriver.ChromeOptions:
        """
        method:
            Before launch spider, set chrome option to accelerate the speed.
        :return:
        """
        # 无图模式 #1允许所有图片；2阻止所有图片；3阻止第三方服务器图片
        prefs = {'profile.default_content_setting_values': {'images': 2}}
        options = webdriver.ChromeOptions()  # chrome设置
        options.add_experimental_option('prefs', prefs)
        options.add_argument("disable-cache")
        # 启动浏览器的时候不想看的浏览器运行，那就加载浏览器的静默模式，让它在后台偷偷运行。用headless
        # option.add_argument('headless')
        return options

    @staticmethod
    def access_taobao(browser: selenium.webdriver.Chrome):
        # 淘宝
        browser.get('http://www.taobao.com')
        input_view = browser.find_element(By.ID, 'q')
        input_view.send_keys('U盘')
        button = browser.find_element(By.CLASS_NAME, 'search-button').find_element(By.TAG_NAME, 'button')
        if button is None:
            print('Get button failed')
        else:
            button.click()

    @staticmethod
    def access_jd(browser: selenium.webdriver.Chrome):
        # 京东
        browser.get('http://www.jd.com')
        input_view = browser.find_element(By.ID, 'key')
        input_view.send_keys('U盘')
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

    def get_jd_commodity_from_detail_page(self, browser: selenium.webdriver.Chrome) -> (Commodity, None):
        """
        method:
            Rely the supplied jd commodity detail page. the method format read in info and then return a
            commodity instance.
        :param
            browser: an instance of browser which includes Chrome/Edge/FireFox etc.
            cautiously, the browser current page must be a commodity page.
        :return:
        """
        # TODO:判断是否是详情页，且有可能长时间未响应/无货/链接无效
        comm = Commodity()
        # 获取商品url,可能失败
        try:
            comm.item_url = browser.current_url
        except TimeoutException as err:
            logging.warning('Get url failed! at method:JdDetailReader.get_jd_commodity_from_detail_page()')
            return None
        # 获取商品title
        comm.item_title = browser.title
        # 获取商品name
        comm.item_name = self.get_jd_item_name_from_detail_page(browser)
        # 获取商品分类
        comm.item_type = self.get_jd_item_type_from_detail_page(browser)
        # keyword 从分类中截取
        comm.keyword = comm.item_type[0: comm.item_type.index('>')]
        # 获取店铺url
        comm.store_url = self.get_jd_store_url_from_detail_page(browser)
        # 获取店铺名
        comm.store_name = self.get_jd_store_name_from_detail_page(browser)
        return comm

    def get_jd_item_from_detail_page(self, browser: selenium.webdriver.Chrome) -> (Item, None):
        """
        method:
            Rely the supplied jd item detail page. the method format read in info and then return a
            item instance.
        :param
            browser: an instance of browser which includes Chrome/Edge/FireFox etc.
            cautiously, the browser current page must be a commodity detail page.
        :return:
        """
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
        # 获取商品url,可能失败
        try:
            item.url = browser.current_url
        except TimeoutException:
            logging.warning('Get url failed! at method:JdDetailReader.get_jd_item_from_detail_page()')
            return None
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


class JdListPageReader:
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_list_page_goods_list_xpath = "//div[id=\'J_goodsList\']/ul/*"  # 搜索结果商品列表DOM SET
    __jd_list_page_turn_xpath = "//div[class=\'page clearfix\']//span[class=\'p-num\']/*"  # 翻页按钮
    # 以下xpath必须配合__jd_list_page_goods_list_xpath使用
    __jd_list_page_price_xpath = "//div[class=\'p-price\']/strong/i"  # 价格
    __jd_list_page_item_name_xpath = "//div[class=\'p-name p-name-type-2\']/a/em"  # 商品名
    __jd_list_page_item_url_xpath = "//div[class=\'p-name p-name-type-2\']/a"  # 商品url
    __jd_list_page_sales_amount_xpath = "//div[class=\'p-commit\']/strong/a"  # 销量
    __jd_list_page_store_name_xpath = "//div[class=\'p-shop\']/span/a"  # 店铺名
    __jd_list_page_store_url_xpath = "//div[class=\'p-shop\']/span/a"  # 店铺url

    def __init__(self) -> None:
        super().__init__()

    def get_jd_commodities_from_list_page(self, browser: selenium.webdriver.Chrome, keyword: str) -> list:
        """
        method:
            Rely the supplied jd commodity detail page. the method format read in info and then return a
            commodity instance.
        :param
            browser: an instance of browser which includes Chrome/Edge/FireFox etc.
            cautiously, the browser current page must be a commodity page.
        :return:
            a commodity instance.
        """
        # TODO:判断是否是详情页，且有可能长时间未响应/无货/链接无效
        goods_dom_list = self.get_jd_list_page_goods_list(browser)
        goods_list = []
        for goods_dom in goods_dom_list:
            # 读取单个commodity
            comm = self.get_jd_list_page_single_goods_commodity(browser, goods_dom)
            if comm is not None:
                comm.keyword = keyword
                goods_list.append(comm)
        return goods_list

    def get_jd_item_from_list_page(self, browser: selenium.webdriver.Chrome) -> list:
        """
        method:
            Rely the supplied jd item detail page. the method format read in info and then return a
            item instance.
        :param
            browser: an instance of browser which includes Chrome/Edge/FireFox etc.
            cautiously, the browser current page must be a commodity detail page.
        :return:
        """
        # TODO:判断是否是详情页，且有可能长时间未响应/无货/链接无效
        goods_dom_list = self.get_jd_list_page_goods_list(browser)
        item_list = []
        for goods_dom in goods_dom_list:
            # 读取单个item
            item = self.get_jd_list_page_single_goods_items(browser, goods_dom)
            if item is not None:
                item_list.append(item)
        return item_list

    def get_jd_list_page_goods_list(self, browser: selenium.webdriver.Chrome) -> list:
        return browser.find_elements(By.XPATH, self.__jd_list_page_goods_list_xpath)

    def get_jd_list_page_single_goods_commodity(self, browser: selenium.webdriver.Chrome, element: WebElement) \
            -> (Commodity, None):
        """
        :param browser:
        :param element:
        :return:
            An instance of Commodity which haven't set the value of keyword
            or None, if an error occurred.
        """
        # 获取商品url,可能失败
        comm = Commodity()
        try:
            comm.item_url = browser.current_url
        except TimeoutException:
            logging.warning('Get url failed! at method:JdListPageReader.get_jd_list_page_single_goods_commodity()')
            return None
        # XXX: Keyword未指定

        # 获取商品title
        comm.item_title = browser.title
        # 获取商品name
        comm.item_name = self.get_jd_item_name_from_list_page(element)
        # 获取商品分类（列表下是不存在的）
        # 获取店铺url
        comm.store_url = self.get_jd_store_url_from_list_page(element)
        # 获取店铺名
        comm.store_name = self.get_jd_store_name_from_list_page(element)
        return comm

    def get_jd_list_page_single_goods_items(self, browser: selenium.webdriver.Chrome, element: WebElement) \
            -> (Item, None):
        """

        :param browser:
        :param element:
        :return:
            An instance of Item or None, if an error occurred.
        """
        item = Item()
        # 起止时间
        item.data_begin_time = item.data_end_time = time.time()
        # 获取颜色标题及所选项目值（详情列表不存在的）
        # 获取版本标题及所选项目值（详情列表不存在的）
        # 获取价格
        item.price = self.get_jd_price_from_list_page(element)
        # 获取plus会员价格（详情列表不存在的）
        # 获取商品url,可能失败
        try:
            item.url = browser.current_url
        except TimeoutException:
            logging.warning('Get url failed! at method:JdListPageReader.get_jd_list_page_single_goods_item()')
            return None
        # 领券（详情列表不存在的）
        # 库存:京东不显示库存量，只有有无货之分（详情列表不存在的）
        # 快递费:京东各省价格均不同，有货情况也不同故不做记录（详情列表不存在的）
        # 销量
        item.sales_amount = self.get_jd_sales_amount_from_list_page(element)
        # 可选字段（详情列表不存在的）
        # 生成所有字段（详情列表不存在的）
        item.generate_all_specification()
        return item

    def get_jd_store_name_from_list_page(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_store_name_xpath).text.strip()

    def get_jd_store_url_from_list_page(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_store_name_xpath).get_attribute('href')

    def get_jd_item_name_from_list_page(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_item_name_xpath).text.strip()

    def get_jd_sales_amount_from_list_page(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_sales_amount_xpath).text[0: -1].strip()

    def get_jd_price_from_list_page(self, element: WebElement) -> float:
        try:
            return float(element.find_element(By.XPATH, self.__jd_list_page_price_xpath).text)
        except ValueError:
            return -1


class DatabaseHelper:
    __sql_insert_commodity = "INSERT INTO COMMODITY(item_url_md5,item_url, item_title," \
                             "item_name, item_type, keyword, store_name, store_url) " \
                             "VALUE ('%s','%s','%s','%s','%s','%s','%s','%s');"
    __sql_insert_item = "INSERT INTO ITEM(item_url_md5,item_url,data_begin_time,data_end_time," \
                        "item_price,plus_price, ticket, inventory, sales_amount, transport_fare," \
                        "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
                        "VALUE ('%s','%s',%f,%f,%f,%f,'%s',%d,'%s',%f" \
                        ",'%s','%s','%s','%s','%s','%s','%s');"
    __sql_query_commodity = "SELECT * FROM commodity " \
                            "WHERE item_url_md5='%s';"
    __sql_query_item = "SELECT * FROM item " \
                       "WHERE item_url_md5='%s' " \
                       "ORDER BY data_begin_time DESC " \
                       "LIMIT 1;"  # 选取最顶上一条记录即可
    __sql_update_item = "UPDATE item " \
                        "SET data_end_time=%f " \
                        "WHERE item_url_md5='%s' and data_begin_time=%f and item_price=%f ;"
    __connection = None

    def __init__(self):
        __connection = self.__get_mysql_connection()

    def __del__(self):
        if self.__connection is not None and self.__is_mysql_connect_valid(self.__connection):
            self.__connection.close()  # 关闭连接

    def __get_mysql_connection(self) -> pymysql.connections.Connection:
        """
        仅供类内部使用，不能开放接口给外界读取，防止恶意关闭连接！
        DO NOT use the method in outside, it could lead to unexpected ERROR!
        :return:
            a member connection of mysql, it confirm are alive.
        """
        if self.__connection is None:
            # TODO:从外部文件读入用户名/密码/host！
            self.__connection = pymysql.connect(
                user='root', password='mysql233', charset='utf8',
                database='ec_spider', use_unicode=True
            )
        # 防止之前关闭，重新连接
        self.__connection.ping(True)
        return self.__connection

    @staticmethod
    def __is_mysql_connect_valid(connect: pymysql.connections.Connection) -> bool:
        """
        method:
            detect whether the supplied mysql connection alive.
        :param connect:
        :return:
        """
        try:
            connect.ping(False)
        except pymysql.err.Error:
            return False
        return True

    def insert_commodity(self, commodity: Commodity):
        """
        method:
            save gave commodity info into mysql database.
        :param
            commodity: instance of Commodity, you must be confirm commodity.item_url not None.
        :return:
        """
        if type(commodity) != Commodity:
            return
        # TODO:检查是否存在,是的话看看能否补全信息，而后跳过
        if self.is_commodity_exist(commodity.item_url_md5):
            logging.info('Url_md5:', commodity.item_url_md5, ' existed in database.')
            return
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_insert_commodity % (
                commodity.item_url_md5, commodity.item_url, commodity.item_title, commodity.item_name,
                commodity.item_type, commodity.keyword, commodity.store_name, commodity.store_url
            ))
            self.__connection.commit()

    def insert_item(self, item: Item):
        """
        method:
            save gave item info into mysql database.
        :param
            item: instance of Item, you must be confirm item.item_url and item.data_date not None.
        :return:
        """
        if type(item) != Item:
            return
        with self.__connection.cursor() as cursor:
            if self.is_item_price_changes(item):
                # TODO:存在,的话看看能否补全信息
                # TODO:这里item的起始时间已经不是当前时间了，通过is_item_price_changes()方法
                #  XXX:已经改为了最新记录的起始时间，这样下面那句查询才能成功定位到该条记录，进而更新
                cursor.execute(self.__sql_update_item % (
                    item.data_end_time, item.item_url_md5, item.data_begin_time, item.price))
                self.__connection.commit()
                return
            cursor.execute(self.__sql_insert_item % (
                item.item_url_md5, item.url, item.data_begin_time, item.data_end_time, item.price, item.plus_price,
                item.ticket, item.inventory, item.sales_amount, item.transport_fare, item.all_specification,
                item.spec1, item.spec2, item.spec3, item.spec4, item.spec5, item.spec_other
            ))
            self.__connection.commit()

    def is_commodity_exist(self, commodity_md5: str) -> bool:
        if self.__connection.query(self.__sql_query_commodity % (commodity_md5,)) > 0:
            return True
        return False

    def is_item_price_changes(self, item: Item) -> bool:
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_query_item % (item.item_url_md5,))
            row = cursor.fetchone()
            if row is None:
                logging.warning('Query record error at DatabaseHelper.is_item_price_changes()'
                                '\nget row is None\n', item.__str__())
                return False
            if item.price == row[4]:
                # TODO:
                #  XXX:这里将之前记录的起始时间传递出去，下一步更新时才方便查找该条记录
                item.data_begin_time = row[2]
                return True
        return False


if __name__ == '__main__':
    laun = Launcher()
    helper = DatabaseHelper()
    jddr = JdDetailPageReader()
    with webdriver.Chrome(chrome_options=laun.chrome_option_initial()) as chrome_test:
        chrome_test.set_page_load_timeout(10)  # 等待10秒
        # ############# 当初的少年怎么也不会想到
        laun.anti_detected_initial(chrome_test)
        try:
            chrome_test.get('https://item.jd.com/8735304.html#none')
        except TimeoutException:
            logging.info('Browser timeout!')
        commo = jddr.get_jd_commodity_from_detail_page(chrome_test)
        ite = jddr.get_jd_item_from_detail_page(chrome_test)
        helper.insert_commodity(commo)
        helper.insert_item(ite)
        time.sleep(10)

# https://item.jd.com/8735304.html#none
# http://item.jd.com/20742438990.html # 只有商品颜色选择
# http://item.jd.com/28252543502.html # 优惠券
# https://item.jd.com/35165938134.html # plus
