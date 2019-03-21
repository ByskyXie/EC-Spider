function setContent(content){
//    window.location.replace();
    document.getElementById('priceMap').innerHTML = content;
}

function setData(dat){
    if(typeof dat == "string"){
        dat = dat.split('|');  //转化为数组对象
        for (var i=0;i<dat.length;i++){
            dat[i] = jQuery.parseJSON(dat[i]);   //转换为JSON对象
        }
    }
    var data = [{
     disp:'1900-01-01',
     value: 0.0
    }, {
     disp:'2050-01-01',
     value: 0.0
    } ];
    if(dat.length != 0)
        data = dat;
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
}

function getData(url){
//TODO:考虑上传价格信息
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "http://localhost:8080/server/popup?json="+url,true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = function(){
        if(xhr.readyState == xhr.DONE){
            if(xhr.status == 200){
                setData(xhr.responseText);
            }
            else
                setContent("Code:"+xhr.status);
        }
    }
    xhr.send();
}

document.body.clientHeight;

chrome.tabs.getSelected(null, function (tab) {
    //运行入口
    getData(tab.url);  //tab.url获取当前URL
});


