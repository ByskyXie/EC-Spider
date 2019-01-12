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
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement


class Launcher:

    def __init__(self) -> None:
        super().__init__()

    def launch_spider(self):
        """
        method:
            The EC-Spider's entrance. you could selected scratch TaoBao/Tmall or jd.
        :param
            ec_list:
        :return:
        """
        with webdriver.Chrome(chrome_options=laun.chrome_option_initial()) as chrome:
            chrome.implicitly_wait(10)  # 等待10秒
            self.anti_detected_initial(chrome)
            # 1.根据搜索列表不断更新价格信息或是新增商品
            keyword_list = self.get_commodity_type_list()
            # 访问京东
            self.access_jd(chrome, keyword_list)
            # 访问淘宝

            # 2.针对未更新但已有记录的商品，也更新
            # jddr = JdDetailPageReader()
            # commo = jddr.get_jd_commodity_from_detail_page(chrome)
            # ite = jddr.get_jd_item_from_detail_page(chrome)
            # helper.insert_commodity(commo)
            # helper.insert_item(ite)
            # 3.若此轮执行耗时超过预计时间，进行商品的删除操作。删除依据为（销量，近期访问次数）
            # 4.检查是否满足清除次数的条件，为真则利用SQL语句集体清空

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
        # options.add_argument('headless')
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
    def access_jd(browser: selenium.webdriver.Chrome, kw_list: list):
        # 京东
        helper = DatabaseHelper()
        jlpr = JdListPageReader()
        #############
        try:
            browser.get('http://www.jd.com')
        except TimeoutException:
            logging.info('Browser timeout!')
        for kw in kw_list:
            input_view = browser.find_element(By.ID, 'key')
            input_view.send_keys(kw)
            # TODO:可能出现"抱歉，没有找到与“POS机”相关的商品"
            button = browser.find_element(By.XPATH, '//*[@class=\'search-m\']').find_element(By.CLASS_NAME, 'button')
            browser.execute_script("""   
                if (navigator.webdriver) {
                    navigator.webdrivser = false;
                    delete navigator.webdrivser;
                    Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
                }""")  # 检测无头模式，为真则做出修改
            if button is None:
                logging.warning('Get button failed:', browser.current_url)
            else:
                button.click()
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # TODO:初始化，设置显式等待减少加载时间。等待60条记录全出现后再读取
            commodity_list = jlpr.get_jd_commodities_from_list_page(browser, kw)
            helper.insert_commodities(commodity_list)
            item_list = jlpr.get_jd_items_from_list_page(browser)
            helper.insert_items(item_list)
            # TODO:读取结束后翻页，记录页码

    def get_commodity_type_list(self) -> list:
        list = []
        # 从外部文件读取搜索列表
        return list


class JdDetailPageReader:
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_detail_page_detect = "//div[@class=\'product-intro clearfix\']/div[@class=\'itemInfo-wrap\']"
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
        # TODO:有可能无货/链接无效
        if not self.is_current_page_is_jd_detail(browser):
            logging.info("[JdDetailPageReader.get_jd_commodity_from_detail_page]"
                         " Current page is't detail page:", browser.title)
            return None  # 判断是否是详情页
        comm = Commodity()
        # 获取商品url,可能失败
        try:
            comm.item_url = browser.current_url
        except TimeoutException:
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
        # 默认访问次数为0
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
        # TODO:有可能无货/链接无效
        if not self.is_current_page_is_jd_detail(browser):
            logging.info("[JdDetailPageReader.get_jd_item_from_detail_page]"
                         " Current page is't detail page:", browser.title)
            return None  # 判断是否是详情页
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
        # 获取商品url,可能因加载中等失败
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

    def is_current_page_is_jd_detail(self, browser: selenium.webdriver.Chrome):
        try:
            browser.find_element(By.XPATH, self.__jd_detail_page_detect)
        except selenium.common.exceptions.NoSuchElementException:
            return False
        return True

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

    def get_jd_remark_from_detail_page(self, browser: selenium.webdriver.Chrome) -> int:
        remark = browser.find_element(By.XPATH, self.__jd_detail_page_remark_xpath).text[1: -1]
        if len(remark) > 1:
            remark = remark[:-1]  # 说明销量不为个位数
        amount = 0.0
        try:
            amount = float(remark)  # 这里用于识别个位数销量
        except ValueError:
            suffix = remark[-1:]
            if suffix == '+':
                amount = float(remark[:-1])
            if suffix == '万':
                amount = float(remark[:-1]) * 10000
            elif suffix == '亿':
                amount = float(remark[:-1]) * 100000000
        return int(amount)

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

    __jd_sales_amount_limit = 3000  # 高于该销量的商品才记录
    # 商品属性对应xpath 考虑优先从外部文本文件读入，方便服务器端维护
    __jd_list_page_detect = "//div[@id=\'J_main\']//div[@id=\'J_goodsList\']"
    __jd_list_page_goods_list_xpath = "//div[@id=\'J_goodsList\']/ul/*"  # 搜索结果商品列表DOM SET
    __jd_list_page_turn_xpath = "//div[@class=\'page clearfix\']//span[@class=\'p-num\']/*"  # 翻页按钮
    # 以下xpath必须配合__jd_list_page_goods_list_xpath使用
    __jd_list_page_price_xpath = ".//div[@class=\'p-price\']/strong/i"  # 价格
    __jd_list_page_item_name_xpath = ".//div[@class=\'p-name p-name-type-2\']/a/em"  # 商品名
    __jd_list_page_item_url_xpath = ".//div[@class=\'p-name p-name-type-2\']/a"  # 商品url
    __jd_list_page_sales_amount_xpath = ".//div[@class=\'p-commit\']/strong/a"  # 销量
    __jd_list_page_store_name_xpath = ".//div[@class=\'p-shop\']/span/a"  # 店铺名
    __jd_list_page_store_url_xpath = ".//div[@class=\'p-shop\']/span/a"  # 店铺url

    def __init__(self) -> None:
        super().__init__()

    @property
    def jd_sales_amount_limit(self):
        return self.__jd_sales_amount_limit

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
        # TODO:有可能长时间未响应
        goods_list = []
        if not self.is_current_page_is_jd_list(browser):
            return goods_list  # 判断是否是详情页
        goods_dom_list = self.get_jd_list_page_goods_list(browser)
        for goods_dom in goods_dom_list:
            # 读取单个commodity，查看是否符合销量限制
            remark = self.get_jd_sales_amount_from_list_page(goods_dom)
            if remark < self.jd_sales_amount_limit:
                continue
            # 读取
            comm = self.get_jd_list_page_single_goods_commodity(goods_dom)
            if comm is not None:
                # 补全keyword，通过哪个关键字搜到的
                comm.keyword = keyword
                goods_list.append(comm)
        return goods_list

    def get_jd_items_from_list_page(self, browser: selenium.webdriver.Chrome) -> list:
        """
        method:
            Rely the supplied jd item detail page. the method format read in info and then return a
            item instance.
        :param
            browser: an instance of browser which includes Chrome/Edge/FireFox etc.
            cautiously, the browser current page must be a commodity detail page.
        :return:
        """
        item_list = []
        # TODO:有可能长时间未响应
        if not self.is_current_page_is_jd_list(browser):
            return item_list  # 判断是否是详情页
        goods_dom_list = self.get_jd_list_page_goods_list(browser)
        for goods_dom in goods_dom_list:
            # 读取单个commodity，查看是否符合销量限制
            remark = self.get_jd_sales_amount_from_list_page(goods_dom)
            if remark < self.jd_sales_amount_limit:
                continue
            # 读取单个item
            item = self.get_jd_list_page_single_goods_items(goods_dom)
            if item is not None:
                item_list.append(item)
        return item_list

    def is_current_page_is_jd_list(self, browser: selenium.webdriver.Chrome) -> bool:
        try:
            browser.find_element(By.XPATH, self.__jd_list_page_detect)
        except selenium.common.exceptions.NoSuchElementException:
            return False
        return True

    def get_jd_list_page_goods_list(self, browser: selenium.webdriver.Chrome) -> list:
        return browser.find_elements(By.XPATH, self.__jd_list_page_goods_list_xpath)

    def get_jd_list_page_single_goods_commodity(self, element: WebElement) \
            -> (Commodity, None):
        """
        :param
            element:A item of the list witch gain by method: get_jd_list_page_goods_list().
        :return:
            An instance of Commodity which haven't set the value of keyword
            or None, if an error occurred.
        """
        # 获取商品url,可能失败
        comm = Commodity()
        comm.item_url = self.get_jd_item_url_from_list_page(element)
        # XXX: Keyword未指定

        # 获取商品title
        comm.item_title = self.get_jd_item_name_from_list_page(element)
        # 获取商品name
        comm.item_name = comm.item_title
        # 获取商品分类（列表下是不存在的）
        # 获取店铺url
        comm.store_url = self.get_jd_store_url_from_list_page(element)
        # 获取店铺名
        comm.store_name = self.get_jd_store_name_from_list_page(element)
        # 默认访问次数为0
        return comm

    def get_jd_list_page_single_goods_items(self, element: WebElement) \
            -> (Item, None):
        """
        :param element:
            A item of the list witch gain by method: get_jd_list_page_goods_list().
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
        # 获取商品url
        item.url = self.get_jd_item_url_from_list_page(element)
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

    def get_jd_item_url_from_list_page(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_item_url_xpath).get_attribute('href')

    def get_jd_sales_amount_from_list_page(self, element: WebElement) -> int:
        remark = element.find_element(By.XPATH, self.__jd_list_page_sales_amount_xpath).text
        if len(remark) > 1:
            remark = remark[:-1]  # 说明销量不为个位数
        amount = 0.0
        try:
            amount = float(remark)  # 这里用于识别个位数销量
        except ValueError:
            suffix = remark[-1:]
            if suffix == '+':
                amount = float(remark[:-1])
            if suffix == '万':
                amount = float(remark[:-1]) * 10000
            elif suffix == '亿':
                amount = float(remark[:-1]) * 100000000
        return int(amount)

    def get_jd_price_from_list_page(self, element: WebElement) -> float:
        try:
            return float(element.find_element(By.XPATH, self.__jd_list_page_price_xpath).text)
        except ValueError:
            return -1


class DatabaseHelper:
    __sql_insert_commodity = "INSERT INTO COMMODITY(item_url_md5,item_url, item_title," \
                             "item_name, item_type, keyword, store_name, store_url, access_num) " \
                             "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s',%d);"
    __sql_insert_commodities = "INSERT IGNORE INTO COMMODITY(item_url_md5,item_url, item_title," \
                               "item_name, item_type, keyword, store_name, store_url, access_num) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"  # # insert_many需要%s占位,IGNORE/REPLACE关键字
    __sql_insert_item = "INSERT INTO ITEM(item_url_md5,item_url,data_begin_time,data_end_time," \
                        "item_price,plus_price, ticket, inventory, sales_amount, transport_fare," \
                        "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
                        "VALUES ('%s','%s',%f,%f,%f,%f,'%s',%d,'%d',%f" \
                        ",'%s','%s','%s','%s','%s','%s','%s');"
    __sql_insert_items = "INSERT IGNORE INTO ITEM(item_url_md5,item_url,data_begin_time,data_end_time," \
                         "item_price,plus_price, ticket, inventory, sales_amount, transport_fare," \
                         "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
                         "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" \
                         ",%s,%s,%s,%s,%s,%s,%s);"  # insert_many需要%s占位，可以用REPLACE关键字
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
        DO NOT use the method at outside, it could lead to unexpected ERROR!
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
        :param
            connect: An instance of pymysql.connections.Connection
        :return:
        """
        try:
            connect.ping(False)
        except pymysql.err.Error:
            return False
        return True

    def refresh_items(self):
        pass  # TODO:针对已记录且未在当日搜索结果的商品，应该另起一个线程处理该情况

    def insert_commodities(self, commodity_list: list):
        if type(commodity_list) is not list or len(commodity_list) == 0 \
                or type(commodity_list[0]) is not Commodity:
            return
        with self.__connection.cursor() as cursor:
            try:
                cursor.executemany(self.__sql_insert_commodities
                                   , self.__general_nesting_commodity_list(commodity_list))
                assert cursor.rowcount == len(commodity_list), 'Not all commodities insert success.'
                self.__connection.commit()
            except Exception:
                logging.info('Insert commodities occurred error.', traceback.print_exc())

    @staticmethod
    def __general_nesting_commodity_list(commodity_list: list) -> list:
        nesting_list = []
        for commodity in commodity_list:
            nesting_list.append(
                (commodity.item_url_md5, commodity.item_url, commodity.item_title,
                 commodity.item_name, commodity.item_type, commodity.keyword,
                 commodity.store_name, commodity.store_url, commodity.access_num))
        return nesting_list

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
                commodity.item_type, commodity.keyword, commodity.store_name, commodity.store_url, commodity.access_num
            ))
            self.__connection.commit()

    def insert_items(self, item_list: list):
        if type(item_list) is not list or len(item_list) == 0 \
                or type(item_list[0]) is not Item:
            return
        with self.__connection.cursor() as cursor:
            try:
                cursor.executemany(self.__sql_insert_items, self.__general_nesting_item_list(item_list))
                assert cursor.rowcount == len(item_list), 'Not all items insert success.'
                self.__connection.commit()
            except Exception:
                logging.info('Insert items occurred error.', traceback.print_exc())

    @staticmethod
    def __general_nesting_item_list(item_list: list) -> list:
        nesting_list = []
        for item in item_list:
            nesting_list.append(
                (item.item_url_md5, item.url, item.data_begin_time, item.data_end_time,
                 item.price, item.plus_price, item.ticket, item.inventory, item.sales_amount,
                 item.transport_fare, item.all_specification, item.spec1, item.spec2,
                 item.spec3, item.spec4, item.spec5, item.spec_other))
        return nesting_list

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
            # 批量导入，list内元素必须为tuple:(value1,value2,value3...)
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
        """
        method:
            Judge current price whether changed. In the other words, is the least record price equals item.price
        :param
            item: An instance of Item
        :return:
        """
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_query_item % (item.item_url_md5,))
            row = cursor.fetchone()
            if row is None:
                logging.warning('Query record error at DatabaseHelper.is_item_price_changes()'
                                '\nget row is None\n', item.__str__())
                # 说明之前未记录该商品信息
                return False
            if item.price == row[4]:
                # TODO:
                #  XXX:这里将之前记录的起始时间传递出去，下一步更新时才方便查找该条记录
                item.data_begin_time = row[2]
                return True
        return False


if __name__ == '__main__':
    laun = Launcher()
    laun.launch_spider()
    print('Finished.')

# https://item.jd.com/8735304.html#none
# http://item.jd.com/20742438990.html # 只有商品颜色选择
# http://item.jd.com/28252543502.html # 优惠券
# https://item.jd.com/35165938134.html # plus
# https://search.jd.com/Search?keyword=u%E7%9B%98&enc=utf-8&wq=upan&pvid=95acc7c91d22499fba0252857fb31a7e # 搜U盘
