if (navigator.webdriver) {
    navigator.webdrivser = false;
    delete navigator.webdrivser;
    //Make Headless=false
    Object.defineProperty(navigator, 'webdriver', {get: () => false,});
}