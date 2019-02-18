import sys
import time
import json
import smtplib
import hashlib
import threading
import logging
import pymysql
import selenium
import traceback
import exception
import mitmproxy.http
from entity import Item
from entity import Commodity
from email.header import Header
from email.mime.text import MIMEText
import custom_expected_conditions as CEC
from selenium import webdriver
from typing import Optional, Callable, Any, Iterable, Mapping
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement


class Launcher:
    __jd_max_turn_page_amount = 20  # 对于某个关键字最大翻页次数
    __jd_max_wait_time = 20  # 网页加载最大等待时间
    __jd_no_result_str = "没有找到"  # 无结果页面关键字
    __round_begin_time = time.time()  # 一轮爬虫开始时间
    __round_max_duration = 24*60*60  # 一轮最大可接受时间
    __jd_max_duration = __round_max_duration * 1  # 京东分配到的时间
    __tb_max_duration = __round_max_duration * 0

    __thread_pool = []  # 线程池
    __helper = None

    def __init__(self) -> None:
        self.__helper = DatabaseHelper()
        super().__init__()

    def launch_spider(self, auto_mode=False):
        """
        method:
            The EC-Spider's entrance. you could selected scratch TaoBao/Tmall or jd.
        :param
            ec_list:
        :return:
        """
        while True:
            self.__round_begin_time = time.time()  # 计时开始
            with webdriver.Chrome(chrome_options=self.chrome_option_initial()) as chrome:
                chrome.maximize_window()
                self.__thread_pool = []  # 清空线程池
                chrome.implicitly_wait(5)  # 等待5秒
                self.anti_detected_initial(chrome)
                # 1.根据搜索列表不断更新价格信息或是新增商品
                keyword_list = self.get_commodity_type_list()
                # 访问京东
                try:
                    self.access_jd(chrome, keyword_list)
                except (TimeoutException, StaleElementReferenceException):
                    logging.error("[Launcher.launch_spider()]:JD Result page haven't appear or stable although refresh!"
                                  + (traceback.print_exc() or "None"))
                    # 依然失败，需要介入
                    link = LinkAdministrator()
                    link.send_message("[EC-Spider shut down]", "[Launcher.access_jd()]:JD Result page haven't "
                                      "appear although refresh!" + (traceback.print_exc() or "None"))
                    break
                # 访问淘宝
                # self.access_taobao(chrome, keyword_list)
                # 3.若此轮执行耗时超过预计时间，进行商品的删除操作。删除依据为（销量，近期访问次数）
                # 4.检查是否满足清除次数的条件，为真则利用SQL语句集体清空
            # 等待一轮结束
            for thr in self.__thread_pool:
                thr.join()
            # 记录爬虫总使用时间
            self.output_spider_state()
            if not auto_mode:
                break
            blank_time = self.__round_max_duration - time.time() + self.__round_begin_time
            if blank_time > 0:
                # 说明超前完成任务
                time.sleep(blank_time)
            else:
                logging.warning('Full spent timeout:' + str(- blank_time) + 'Second.')

    @staticmethod
    def anti_detected_initial(browser: selenium.webdriver.Chrome):
        """
        method:
            hide selenium features and then pass the spider detection.
        :param
            browser is an instance of browser which includes Chrome/Edge/FireFox etc.
        :return:
        """
        with open('script/anti_detect_strategy.js', 'r') as strategy:
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

    def access_taobao(self, browser: selenium.webdriver.Chrome, kw_list: list):
        # 淘宝
        browser.get('http://www.taobao.com')
        input_view = browser.find_element(By.ID, 'q')
        input_view.send_keys('U盘')
        button = browser.find_element(By.CLASS_NAME, 'search-button').find_element(By.TAG_NAME, 'button')
        if button is None:
            print('Get button failed')
        else:
            button.click()

    def access_jd(self, browser: selenium.webdriver.Chrome, kw_list: list):
        # 京东
        position = 0
        jd_begin_time = time.time()
        jlpr = JdListPageReader()
        wdw = WebDriverWait(browser, self.__jd_max_wait_time, 0.7)
        #############
        try:
            browser.get('http://www.jd.com')
            wdw.until(CEC.PageViewsAppear(
                [(By.ID, jlpr.jd_search_view_id), (By.XPATH, jlpr.jd_search_button_xpath)]
            ), "Input views not appear")
        except TimeoutException:
            logging.warning("Haven't got every views!" + (traceback.print_exc() or 'None'))
        for kw in kw_list:
            position += 1  # 当前kw位置
            page_num = 1
            input_view = browser.find_element(By.ID, jlpr.jd_search_view_id)
            input_view.clear()
            input_view.send_keys(kw)
            button = browser.find_element(By.XPATH, jlpr.jd_search_button_xpath)
            browser.execute_script("""
                if (navigator.webdriver) {
                    navigator.webdrivser = false;
                    delete navigator.webdrivser;
                    Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
                }""")  # TODO:检测无头模式，为真则做出修改
            try:
                button.click()
            except selenium.common.exceptions.WebDriverException:
                browser.refresh()
                logging.error("Launcher.access_jd() :Button can't click.")
                continue
            while page_num <= self.__jd_max_turn_page_amount:
                if self.__jd_max_duration * position / len(kw_list) < (time.time() - jd_begin_time):
                    # 控制进度。说明该kw超时了，以后的页面不再读取
                    logging.info('[Single keyword running timeout]:' + kw + ' page:' + page_num)
                    break
                try:
                    wdw.until(CEC.PageViewsAppear(
                        [(By.XPATH, jlpr.jd_list_page_goods_list_xpath),
                         (By.XPATH, jlpr.jd_list_page_turn_xpath)]
                    ), "Search result not appear")
                except TimeoutException:
                    browser.refresh()  # 刷新重试一遍
                    wdw.until(CEC.PageViewsAppear(
                        [(By.XPATH, jlpr.jd_list_page_goods_list_xpath),
                         (By.XPATH, jlpr.jd_list_page_turn_xpath)]
                    ), "Search result not appear")
                try:
                    temp = browser.find_element(By.XPATH, '//div[@class=\'notice-search\']')
                    if temp is not None and self.__jd_no_result_str in temp.text:
                        # 出现"抱歉，没有找到与“***”相关的商品"
                        logging.warning("JD没有找到与[" + kw + "]相关的商品", browser.current_url)
                        break
                except NoSuchElementException:
                    # 找不到元素正常，说明该关键字有结果
                    pass
                # 跳转到页面最底部
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # 等待60条记录全出现后再读取
                wdw.until(CEC.ResultAllAppear(), "Wait all result failed.")
                time.sleep(0.4)
                # 读取价格信息并更新
                try:
                    self.__helper.insert_commodities(jlpr.read_commodities(browser, kw))
                    self.__helper.insert_items(jlpr.read_items(browser))
                except StaleElementReferenceException:
                    browser.refresh()
                    logging.warning("Launcher.access_jd(): Not stable." + (traceback.print_exc() or "None"))
                    # 重试一次
                    self.__helper.insert_commodities(jlpr.read_commodities(browser, kw))
                    self.__helper.insert_items(jlpr.read_items(browser))
                # 翻页，页码+1
                browser.find_element(By.XPATH, '/*').send_keys(Keys.RIGHT)
                page_num += 1
            # 2.针对未更新但已有记录的商品，也更新
            # 一个关键字已完毕，针对已记录且未在当日搜索结果的商品，另起线程处理该情况
            dt = DetailThread(self.__round_begin_time, kw)
            dt.start()
            self.__thread_pool.append(dt)

    def get_time_spent_percent(self) -> float:
        return (time.time() - self.__round_begin_time)/self.__round_max_duration

    def output_spider_state(self):
        with open('spiderState.txt', 'w') as output_file:
            # 开始时间
            out_str = '[Spider begin time]:' + time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(self.__round_begin_time))
            output_file.writelines(out_str)
            # 结束时间
            out_str = '[Spider end time]:' + time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            output_file.writelines(out_str)
            # 时长
            time_spent = int(time.time() - self.__round_begin_time)
            out_str = '[Spider time spent]:' + \
                      ('%d:%d:%d' % (time_spent/3600, time_spent/60 % 60, time_spent % 60))
            output_file.writelines(out_str)
            output_file.writelines('[Max Allow Duration]:' + str(self.__round_max_duration))

    def add_keyword(self):
        with open("keywords.txt", encoding='UTF-8') as kwf:
            while True:
                kw = kwf.readline()
                if len(kw) == 0:
                    break
                self.__helper.insert_keyword(kw)

    def get_commodity_type_list(self) -> list:
        return self.__helper.get_keyword_list()


class JdDetailPageReader:
    # TODO:获取完整HTML文档：WebElement.get_attribute("outerHTML")
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

    @property
    def jd_detail_page_detect(self):
        return self.__jd_detail_page_detect

    def read_commodity(self, browser: selenium.webdriver.Chrome) -> (Commodity, None):
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
        if not self.is_jd_detail_page(browser):
            logging.info("[JdDetailPageReader.read_commodity]"
                         " Current page is't detail page:", browser.title)
            return None  # 判断是否是详情页
        comm = Commodity()
        # 获取商品url,可能失败
        try:
            comm.item_url = browser.current_url
        except TimeoutException:
            logging.warning('Get url failed! at method:JdDetailReader.read_commodity()')
            return None
        # 获取商品title
        comm.item_title = browser.title
        # 获取商品name
        comm.item_name = self.get_item_name(browser)
        # 获取商品分类
        comm.item_type = self.get_item_type(browser)
        # keyword 从分类中截取
        comm.keyword = comm.item_type[0: comm.item_type.index('>')]
        # 获取店铺url
        comm.store_url = self.get_store_url(browser)
        # 获取店铺名
        comm.store_name = self.get_store_name(browser)
        # 默认访问次数为0
        return comm

    def read_item(self, browser: selenium.webdriver.Chrome) -> (Item, None):
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
        if not self.is_jd_detail_page(browser):
            logging.info("[JdDetailPageReader.read_item]"
                         " Current page is't detail page:", browser.title)
            return None  # 判断是否是详情页
        item = Item()
        # 获取颜色标题及所选项目值
        color_dom = self.get_color_dom(browser)
        if color_dom is not None and len(color_dom) != 0:
            color_title_str = color_dom[0].text  # 获取标题
            color_selected_str = color_dom[1].find_element(By.CLASS_NAME, "selected").text  # 获取已选值
            item.spec1 = color_title_str + '=' + color_selected_str
        else:
            # 某些单一款不需要选颜色
            pass
        # 获取版本标题及所选项目值
        edition_dom = self.get_edition_dom(browser)
        if edition_dom is not None and len(edition_dom) != 0:
            edition_title_str = edition_dom[0].text
            edition_selected_str = edition_dom[1].find_element(By.CLASS_NAME, "selected").text
            item.spec2 = edition_title_str + '=' + edition_selected_str
        else:
            # 说明不需要选择型号，或者说没有型号信息
            pass
        # 获取商品url,可能因加载中等失败
        try:
            item.url = browser.current_url
        except TimeoutException:
            logging.warning('Get url failed! at method:JdDetailReader.read_item()')
            return None
        # 获取价格
        item.price = self.get_price(browser)
        if item.price == -1:
            logging.warning("JdDetailPageReader:Get price is -1\n" + item.url)
            return None
        # 获取plus会员价格
        item.plus_price = self.get_plus_price(browser)
        # 领券
        ticket_dom = self.get_ticket_dom(browser)
        if ticket_dom is not None and len(ticket_dom) != 0:
            ticket_str = ''
            for ti in ticket_dom:
                ticket_str += ti.text + '\n'
            item.ticket = ticket_str
        # 库存:京东不显示库存量，只有有无货之分
        # 快递费:京东各省价格均不同，有货情况也不同故不做记录
        # 销量
        item.sales_amount = self.get_remark(browser)
        # 可选字段
        # 生成所有字段
        item.generate_all_specification()
        return item

    def is_jd_detail_page(self, browser: selenium.webdriver.Chrome):
        try:
            browser.find_element(By.XPATH, self.__jd_detail_page_detect)
        except NoSuchElementException:
            return False
        return True

    def get_store_name(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_store_name_xpath).text.strip()

    def get_store_url(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_store_name_xpath).get_attribute('href')

    def get_item_name(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_item_name_xpath).text.strip()

    def get_item_type(self, browser: selenium.webdriver.Chrome) -> str:
        return browser.find_element(By.XPATH, self.__jd_detail_page_item_type_xpath).text.strip()

    def get_specification_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_specification_xpath)

    def get_color_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_color_xpath)

    def get_edition_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_edition_xpath)

    def get_ticket_dom(self, browser: selenium.webdriver.Chrome):
        return browser.find_elements(By.XPATH, self.__jd_detail_page_ticket_xpath)

    def get_remark(self, browser: selenium.webdriver.Chrome) -> int:
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

    def get_price(self, browser: selenium.webdriver.Chrome) -> float:
        try:
            return float(browser.find_element(By.XPATH, self.__jd_detail_page_price_xpath).text)
        except (ValueError, NoSuchElementException):
            return -1

    def get_plus_price(self, browser: selenium.webdriver.Chrome) -> float:
        try:
            return float(browser.find_element(By.XPATH, self.__jd_detail_page_plus_price_xpath).text[1:])
        except (ValueError, NoSuchElementException):
            return -1


class JdListPageReader:
    __jd_list_page_goods_list_amount = 60  # TODO：后期可以通过读取加载完成页面的实际显示数量动态调整
    __jd_sales_amount_limit = 100  # 高于该销量的商品才记录，这个销量是否作为低门槛好一些？因为搜索的话电商网站已经优化过了
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
    # 供外部接口调用
    __jd_search_view_id = "key"
    __jd_search_button_xpath = "//div[@class=\'form\']/button"

    def __init__(self) -> None:
        super().__init__()

    @property
    def jd_list_page_goods_list_amount(self):
        return self.__jd_list_page_goods_list_amount

    @property
    def jd_sales_amount_limit(self):
        return self.__jd_sales_amount_limit

    @property
    def jd_search_view_id(self):
        return self.__jd_search_view_id

    @property
    def jd_list_page_turn_xpath(self):
        return self.__jd_list_page_turn_xpath

    @property
    def jd_search_button_xpath(self):
        return self.__jd_search_button_xpath

    @property
    def jd_list_page_goods_list_xpath(self):
        return self.__jd_list_page_goods_list_xpath

    def read_commodities(self, browser: selenium.webdriver.Chrome, keyword: str) -> list:
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
        goods_list = []
        if not self.is_jd_list_page(browser):
            return goods_list  # 判断是否是详情页
        goods_dom_list = self.get_goods_list(browser)
        for goods_dom in goods_dom_list:
            # 读取单个commodity，查看是否符合销量限制
            remark = self.get_sales_amount(goods_dom)
            if remark < self.jd_sales_amount_limit:
                logging.info("[销量太低不予记录商品]：", goods_dom.text)
                continue
            try:
                # 读取
                comm = self.read_single_goods_commodity(goods_dom)
                if comm is None:
                    # 若数据为空，模拟鼠标悬停,等待信息加载完成
                    ActionChains(browser).move_to_element(goods_dom).perform()
                    wdw = WebDriverWait(goods_dom, 3, 0.2)
                    wdw.until(EC.presence_of_element_located((By.XPATH, self.__jd_list_page_store_name_xpath)),
                              "[JdListPagerReader.read_commodities()]: wait timeout.")
                    comm = self.read_single_goods_commodity(goods_dom)
                if comm is not None:
                    # 补全keyword，通过哪个关键字搜到的
                    comm.keyword = keyword
                    goods_list.append(comm)
            except TimeoutException:
                logging.warning("Time out for wait single good.")
            except StaleElementReferenceException:
                logging.warning("JdListPageReader.read_commodities():"
                                "Cause JavaScript changed page, can't read element.")
            continue
        return goods_list

    def read_items(self, browser: selenium.webdriver.Chrome) -> list:
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
        if not self.is_jd_list_page(browser):
            return item_list  # 判断是否是详情页
        goods_dom_list = self.get_goods_list(browser)
        for goods_dom in goods_dom_list:
            # 读取单个commodity，查看是否符合销量限制
            remark = self.get_sales_amount(goods_dom)
            if remark < self.jd_sales_amount_limit:
                logging.info("[销量太低不予记录数据]：", goods_dom.text)
                continue
            try:
                # 读取单个item
                item = self.read_single_goods_item(goods_dom)
                if item is not None:
                    item_list.append(item)
            except StaleElementReferenceException:
                logging.warning("JdListPageReader.read_items():"
                                "Cause JavaScript changed page, can't read element.")
                continue
        return item_list

    def is_jd_list_page(self, browser: selenium.webdriver.Chrome) -> bool:
        try:
            browser.find_element(By.XPATH, self.__jd_list_page_detect)
        except NoSuchElementException:
            return False
        return True

    def get_goods_list(self, browser: selenium.webdriver.Chrome) -> list:
        return browser.find_elements(By.XPATH, self.__jd_list_page_goods_list_xpath)

    def read_single_goods_commodity(self, element: WebElement) \
            -> (Commodity, None):
        """
        :param
            element:A item of the list witch gain by method: get_goods_list().
        :return:
            An instance of Commodity which haven't set the value of keyword
            or None, if an error occurred.
        """
        try:
            # 获取商品url,可能失败
            comm = Commodity()
            comm.item_url = self.get_item_url(element)
            # XXX: Keyword未指定

            # 获取商品title
            comm.item_title = self.get_item_name(element)
            # 获取商品name
            comm.item_name = comm.item_title
            # 获取商品分类（列表下是不存在的）
        except NoSuchElementException:
            logging.warning('[Get single goods, No such element]:' +
                            (element.get_attribute("outerHTML") or "None ") + (traceback.print_exc() or 'None'))
            return None
        try:
            # 获取店铺名
            comm.store_name = self.get_store_name(element)
            # 获取店铺url
            comm.store_url = self.get_store_url(element)
            # 默认访问次数为0
        except NoSuchElementException:
            logging.warning("Get single goods, Can't get store info:" +
                            (element.get_attribute("outerHTML") or "None ") + (traceback.print_exc() or 'None'))
        return comm

    def read_single_goods_item(self, element: WebElement) \
            -> (Item, None):
        """
        :param element:
            A item of the list witch gain by method: get_goods_list().
        :return:
            An instance of Item or None, if an error occurred.
        """
        item = Item()
        # 起止时间
        item.data_begin_time = time.time()
        # 获取颜色标题及所选项目值（详情列表不存在的）
        # 获取版本标题及所选项目值（详情列表不存在的）
        # 获取商品url
        item.url = self.get_item_url(element)
        # 获取价格
        item.price = self.get_price(element)
        if item.price == -1:
            logging.warning("JdListPageReader:Get price is -1\n" + item.url)
            return None
        # 获取plus会员价格（详情列表不存在的）
        # 领券（详情列表不存在的）
        # 库存:京东不显示库存量，只有有无货之分（详情列表不存在的）
        # 快递费:京东各省价格均不同，有货情况也不同故不做记录（详情列表不存在的）
        # 销量
        item.sales_amount = self.get_sales_amount(element)
        # 可选字段（详情列表不存在的）
        # 生成所有字段（详情列表不存在的）
        item.generate_all_specification()
        return item

    def get_store_name(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_store_name_xpath).text.strip()

    def get_store_url(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_store_name_xpath).get_attribute('href')

    def get_item_name(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_item_name_xpath).text.strip()

    def get_item_url(self, element: WebElement) -> str:
        return element.find_element(By.XPATH, self.__jd_list_page_item_url_xpath).get_attribute('href')

    def get_sales_amount(self, element: WebElement) -> int:
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

    def get_price(self, element: WebElement) -> float:
        try:
            return float(element.find_element(By.XPATH, self.__jd_list_page_price_xpath).text)
        except ValueError:
            return -1


class DatabaseHelper:
    __sql_insert_commodity = \
        "INSERT INTO COMMODITY(item_url_md5,item_url, item_title," \
        "item_name, item_type, keyword, store_name, store_url, access_num) " \
        "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s',%d);"
    __sql_insert_commodities = \
        "INSERT IGNORE INTO COMMODITY(item_url_md5,item_url, item_title," \
        "item_name, item_type, keyword, store_name, store_url, access_num) " \
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"  # # insert_many需要%s占位,IGNORE/REPLACE关键字
    __sql_insert_item = \
        "INSERT INTO ITEM(item_url_md5,item_url,data_begin_time,data_latest_time,data_end_time," \
        "item_price,plus_price, ticket, inventory, sales_amount, transport_fare," \
        "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
        "VALUES ('%s','%s',%f,%f,%f,%f,%f,'%s',%d,%d,%f" \
        ",'%s','%s','%s','%s','%s','%s','%s');"
    # __sql_insert_items = \
    #     "INSERT IGNORE INTO ITEM(item_url_md5,item_url,data_begin_time,data_latest_time,data_end_time," \
    #     "item_price,plus_price, ticket, inventory, sales_amount, transport_fare," \
    #     "all_specification, spec1, spec2, spec3, spec4, spec5, spec_other) " \
    #     "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" \
    #     ",%s,%s,%s,%s,%s,%s,%s);"  # insert_many需要%s占位，可以用REPLACE关键字
    __sql_query_commodity = \
        "SELECT * FROM commodity " \
        "WHERE item_url_md5='%s';"
    __sql_query_item = \
        "SELECT * FROM item " \
        "WHERE item_url_md5='%s' " \
        "ORDER BY data_begin_time DESC " \
        "LIMIT 1;"  # 选取最顶上一条记录即可
    __sql_update_item_end_time = \
        "UPDATE item " \
        "SET data_end_time=%f " \
        "WHERE item_url_md5='%s' and data_end_time=%f;"
    __sql_update_item_latest_time = \
        "UPDATE item " \
        "SET data_latest_time=%f " \
        "WHERE item_url_md5='%s' and data_end_time=%f;"
    __sql_before_date = \
        "SELECT DISTINCT t1.item_url,sales_amount,access_num " \
        "FROM item,(SELECT item_url_md5,item_url,access_num FROM commodity) as t1 " \
        "WHERE item.item_url_md5 NOT IN (" \
        "  SELECT item_url_md5 " \
        "  FROM item " \
        "  WHERE data_end_time > %f) " \
        "AND item.item_url_md5 = t1.item_url_md5 " \
        "ORDER BY access_num DESC, sales_amount DESC;"  # 所给日期后均未更新的商品
    __sql_keyword_before_date = \
        "SELECT DISTINCT t1.item_url,t1.item_url_md5 " \
        "FROM item,(SELECT item_url_md5,item_url,access_num,keyword FROM commodity) as t1 " \
        "WHERE item.item_url_md5 NOT IN (" \
        "  SELECT item_url_md5 " \
        "  FROM item " \
        "  WHERE data_end_time > %f) " \
        "AND item.item_url_md5 = t1.item_url_md5 AND t1.keyword='%s' " \
        "ORDER BY access_num DESC, sales_amount DESC;"  # 所给日期后均未更新且关键字为%s的商品
    __sql_delete_commodity = \
        "DELETE FROM commodity " \
        "WHERE item_url_md5='%s';"
    __sql_delete_commodities = \
        "DELETE FROM commodity " \
        "WHERE item_url_md5=%s;"
    __sql_delete_item = \
        "DELETE FROM item " \
        "WHERE item_url_md5='%s';"
    __sql_delete_items = \
        "DELETE FROM item " \
        "WHERE item_url_md5=%s;"
    __sql_get_keyword = \
        "SELECT keyword FROM keyword;"
    __sql_insert_keyword = \
        "INSERT INTO keyword(keyword,update_time) " \
        "VALUES('%s',%f);"
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
            # Tips:从外部文件读入用户名/密码/数据库名
            with open("mysql.txt", encoding='UTF-8') as opt:
                usr = opt.readline().strip()  # first line: username
                pwd = opt.readline().strip()  # second line: password
                db = opt.readline().strip()  # third line: database name
                self.__connection = pymysql.connect(
                    user=usr, password=pwd, charset='utf8',
                    database=db, use_unicode=True
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

    def query_refresh_before_date_items(self, time_stamp=time.time(), keyword=None) -> tuple:
        """
        method: Get items info that haven't update before given time(and keyword).
        :param time_stamp:
        :param keyword:
        :return: list. and the item is item_url_md5.
        """
        with self.__connection.cursor() as cursor:
            if keyword is None:
                cursor.execute(self.__sql_before_date % time_stamp)
            else:  # 给出关键字限定
                cursor.execute(self.__sql_keyword_before_date % (time_stamp, keyword))
            return cursor.fetchall()

    def insert_commodities(self, commodity_list: list):
        if type(commodity_list) is not list or len(commodity_list) == 0 \
                or type(commodity_list[0]) is not Commodity:
            return
        with self.__connection.cursor() as cursor:
            try:
                cursor.executemany(self.__sql_insert_commodities
                                   , self.__general_nesting_commodity_list(commodity_list))
                # assert cursor.rowcount == len(commodity_list), 'Not all commodities insert success.'
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
            return -1
        for item in item_list:
            # 逐一校验插入
            self.insert_item(item)

    # @staticmethod
    # def __general_nesting_item_list(item_list: list) -> list:
    #     nesting_list = []
    #     for item in item_list:
    #         nesting_list.append(
    #             (item.item_url_md5, item.url, item.data_begin_time, item.data_end_time,
    #              item.price, item.plus_price, item.ticket, item.inventory, item.sales_amount,
    #              item.transport_fare, item.all_specification, item.spec1, item.spec2,
    #              item.spec3, item.spec4, item.spec5, item.spec_other))
    #     return nesting_list

    def insert_item(self, item: Item):
        """
        method:
            save gave item info into mysql database.
        :param
            item: instance of Item, you must be confirm item.item_url and item.data_date not None.
        :return:
        """
        if type(item) != Item:
            return -1
        with self.__connection.cursor() as cursor:
            if not self.is_item_price_changed(item, True):
                # 说明已经有记录，且价格未改变
                return -1
            # 导入新记录，list内元素必须为tuple:(value1,value2,value3...)
            try:
                cursor.execute(self.__sql_insert_item % (
                    item.item_url_md5, item.url, item.data_begin_time, item.data_latest_time, item.data_end_time,
                    item.price, item.plus_price, item.ticket, item.inventory, item.sales_amount, item.transport_fare,
                    item.all_specification, item.spec1, item.spec2, item.spec3, item.spec4, item.spec5, item.spec_other
                ))
                self.__connection.commit()
            except pymysql.err.IntegrityError:
                logging.warning("[Item insert error]:", traceback.print_exc())

    def delete_commodity(self, url_md5: str):
        if type(url_md5) is not str:
            return
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_delete_item % url_md5)
            self.__connection.commit()
            cursor.execute(self.__sql_delete_commodity % url_md5)
            self.__connection.commit()

    def delete_commodities(self, url_md5_list: list):
        if len(url_md5_list) < 1 or type(url_md5_list[0]) is not str:
            return
        with self.__connection.cursor() as cursor:
            # 先删除记录才能删商品
            cursor.executemany(self.__sql_delete_items, url_md5_list)
            self.__connection.commit()
            cursor.executemany(self.__sql_delete_commodities, url_md5_list)
            self.__connection.commit()

    def is_commodity_exist(self, commodity_md5: str) -> bool:
        if self.__connection.query(self.__sql_query_commodity % commodity_md5) > 0:
            return True
        return False

    def is_item_price_changed(self, item: Item, if_changed_update_end_time: bool = False) -> bool:
        """
        method:
            Judge current price whether changed. In the other words, is the least record price equals item.price
        :param
            item: An instance of Item
        :return:
        """
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_query_item % item.item_url_md5)
            row = cursor.fetchone()
            if row is None:
                logging.info('Query record error at DatabaseHelper.is_item_price_changed()'
                             '\nget row is None\n' + item.__str__())
                # 说明之前未记录该商品信息
                return True
            # 记录最近访问时间
            cursor.execute(self.__sql_update_item_latest_time % (
                item.data_begin_time, item.item_url_md5, Item.CURRENT_CODE))
            self.__connection.commit()
            if item.price == row[5]:
                return False
            logging.info("[Price changed]:", item.price, "!=", row[5])
            if if_changed_update_end_time:
                # 更新该记录结束时间
                cursor.execute(self.__sql_update_item_end_time % (
                    item.data_begin_time, item.item_url_md5, Item.CURRENT_CODE))
                self.__connection.commit()
        return True

    def get_keyword_list(self) -> list:
        kw_list = []
        with self.__connection.cursor() as cursor:
            cursor.execute(self.__sql_get_keyword)
            for i in cursor.fetchall():
                kw_list.append(i[0])
            return kw_list

    def insert_keyword(self, value: str):
        if type(value) != str:
            return
        with self.__connection.cursor() as cursor:
            try:
                cursor.execute(self.__sql_insert_keyword % (value.strip(), time.time()))
                self.__connection.commit()
            except pymysql.err.IntegrityError:
                pass


class LinkAdministrator:
    __host = 'smtp.qq.com'
    __port = 465
    __reciver = 'byskyxie@qq.com'
    __to = "byskyXie"

    def send_message(self, title: str, msg: str, user: str = None, pwd: str = None):
        if user is None:
            try:
                f = open("smtp.txt")
                user = f.readline()
                pwd = f.readline()
            except FileNotFoundError:
                print("No account info in smtp.txt, Or you can supply param 'user' and 'pwd'")
                return
        message = MIMEText(msg, 'plain', 'utf-8')
        message['Subject'] = Header(title, 'utf-8')
        message['From'] = Header("EC-Spider", 'utf-8')
        message['To'] = Header(self.__to, 'utf-8')
        smtp = smtplib.SMTP()
        smtp.connect(self.__host)
        smtp.login(user, pwd)
        smtp.sendmail(user, self.__reciver, message.as_string())
        smtp.quit()


class DetailThread(threading.Thread):
    __keyword = None
    __round_begin_time = None
    __round_max_end_time = None  # 最久可接受的结束时间，可能因为处理完/中断而提前结束线程
    __max_duration = 20*60  # 该窗口最多开20分钟
    __max_wait_time = 20  # 网页加载最大等待时间
    __runnable_flag = True  # 决定是否继续运行

    def __init__(self, round_begin_time: time, keyword: str, group=None,
                 target=None, name=None, args=(), kwargs=None, *, daemon=None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.__keyword = keyword
        self.__round_begin_time = round_begin_time
        self.__round_max_end_time = round_begin_time + self.__max_duration

    def run(self) -> None:
        jdpr = JdDetailPageReader()
        helper = DatabaseHelper()
        item_list = helper.query_refresh_before_date_items(self.__round_begin_time, self.__keyword)
        with webdriver.Chrome(chrome_options=Launcher.chrome_option_initial()) as chrome:
            chrome.maximize_window()
            wdw = WebDriverWait(chrome, self.__max_wait_time)
            counter = 0
            for it in item_list:
                # 设立时间标志，超时自行退出(访问详情页，效率会特别低)
                if not self.__runnable_flag or self.__round_max_end_time < time.time():
                    break
                try:
                    chrome.get(it[0])
                    wdw.until(EC.presence_of_element_located((By.XPATH, jdpr.jd_detail_page_detect)),
                              "[DetailThread.run()]: wait timeout.")
                    item = jdpr.read_item(chrome)
                    helper.insert_item(item)
                except TimeoutException:
                    logging.info(it[0] + " Cause TimeoutException, haven't record.")
                except NoSuchWindowException:
                    logging.warning("[DetailThread.run()]: Chrome has shut down.")
                    # 因意外打断，此次更新到此为止，不删除未更新的数据
                    return
                counter += 1
        # 删除counter及以后的商品记录
        item_list = item_list[counter:]
        md5_list = []
        for it in item_list:
            md5_list.append(it[1])
        # TODO:未访问达到一定天数就删除
        helper.delete_commodities(md5_list)

    def stop(self):
        self.__runnable_flag = False


if __name__ == '__main__':
    laun = Launcher()
    laun.add_keyword()
    try:
        laun.launch_spider()
    except Exception:
        LinkAdministrator().send_message("EC-Spider shut down", (traceback.print_exc() or 'None'))
    print('Finished.')

# https://item.jd.com/8735304.html#none
# http://item.jd.com/20742438990.html # 只有商品颜色选择
# http://item.jd.com/28252543502.html # 优惠券
# https://item.jd.com/35165938134.html # plus
# https://search.jd.com/Search?keyword=u%E7%9B%98&enc=utf-8&wq=upan&pvid=95acc7c91d22499fba0252857fb31a7e # 搜U盘
