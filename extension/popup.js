function setContent(content){
//    window.location.replace();
    document.getElementById('priceMap').innerHTML = content;
}

function setData(dat){
    data = dat;
}

document.body.clientHeight;
//var bg = chrome.extension.getBackgroundPage();
//jQuery.get('test.html', "item_url="+chrome.tabs.getSelected.url
//    , function (result){ setContent(result); });  //本地文件可嵌入

var data = [{
 disp:'2019-02-18',
value: 79.900000
}, {
 disp:'2019-02-19',
value: 89.900000
} ];

//jQuery.ajax({
//    url:"http://localhost:8080/server/popupjson=https://item.jd.com/5328201.html",
//    type:"GET",
//    dataType: "json",
//    success:function(data){setData(jQuery.parseJSON(data));}
//});
//jQuery.get('http://localhost:8080/server/popup', "json="+"https://item.jd.com/5328201.html"
//    , function (result){ setContent("OK"); setData(jQuery.parseJSON(result)); }, "json");

var xhr = new XMLHttpRequest();
xhr.open("GET", "http://localhost:8080/server/popup?json=https://item.jd.com/5328201.html",true);
xhr.responseType = 'text';
xhr.onreadystatechange = function(){
    if(xhr.readyState == xhr.DONE){
        if(xhr.status == 200){
            setContent("Get:"+xhr.responseText);
            setData(JSON.parse(xhr.responseText));
        }
        else
            setContent("Code:"+xhr.status);
    }
}
xhr.send();


var chart = new G2.Chart({
    container: 'priceMap',
    forceFit: true,
    height: window.innerHeight
});
var defs = {
disp: {
    alias:'Time',
    type:'time',
    tickCount:5,
    range:[0,0.94]
  }
};
chart.source(data, defs);
chart.line().position('disp*value').shape('hv');
chart.render();