
function getDomainFromUrl(url){
    var host = "null";
    if(typeof url == "undefined" || url == null)
        url = window.location.href;
    var regex = /.*\:\/\/([^\/]*).*/;
    var match = url.match(regex);
    if(typeof match != "undefined" && match != null)
        host = match[1];
    return host;
}

function checkWeatherShow(tabId, changeInfo, tab){
    host = getDomainFromUrl(tab.url).toLowerCase();
    if(host == "item.jd.com"  || host == "www.taobao.com" || host == "www.tmall.com"){
        chrome.pageAction.show(tabId);
    }
}

function getServerPage(){
    var views = chrome.extension.getViews({type:["popup","tab"]});
//  获取页面
    var value = $.get('http://localhost:8080/server/popup?item_url=' + views[2].document.URL);
//  更改popup信息
    views[0].document.location = value;
}

chrome.tabs.onUpdated.addListener(checkWeatherShow);
