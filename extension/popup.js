function setDisplayText(txt){
    document.getElementById('display').innerText = txt;
}

var bg = chrome.extension.getBackgroundPage();
console.log(bg.getServerPage);

