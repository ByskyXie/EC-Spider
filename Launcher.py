import sys
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

def Launcher():
    def launch_spider(self):
        pass

if __name__ == '__main__':
    chrome = webdriver.Chrome()
    chrome.get('http://www.taobao.com')
    input = chrome.find_element(By.ID,'q')
    input.send_keys('U盘')
    button = chrome.find_element(By.CLASS_NAME,'search-button').find_element(By.TAG_NAME,'button')
    chrome.execute_script("""
    if (navigator.webdriver) {
        window.alert('Headless is true');
        Object.defineProperty(navigator, 'webdriver', {get: () => false,});//改为Headless=false
    }""")#检测无头模式，为真则做出修改
    if(button is None):
        print('Get none button')
    else:
        button.click()

    print('Finished!')




