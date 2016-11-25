// ==UserScript==
// @name           IntelScript
// @namespace      http://foo.bar.org
// @include        http://foo.bar.org/*
// ==/UserScript==

url = location.href;

if(matches = url.match(/berichte.php\?id=(\d+)\|?(.*)?/)) {
	var id = matches[1];
	var h = matches[2];
	
	var attacker = document.getElementById("attacker");
	var units = attacker.childNodes[2]
	var infos = attacker.childNodes[3]
	
	// attacker player+village id
	var auid = attacker.childNodes[0].childNodes[1].childNodes[3].childNodes[0].attributes[0].nodeValue.match(/uid=(\d+)/)[1]
	var avuid = attacker.childNodes[0].childNodes[1].childNodes[3].childNodes[2].attributes[0].nodeValue.match(/d=(\d+)/)[1]
	
	// defender player+village id
	var duid = attacker.nextSibling.childNodes[1].childNodes[1].childNodes[2].childNodes[0].attributes[0].nodeValue.match(/uid=(\d+)/)[1]
	var dvuid = attacker.nextSibling.childNodes[1].childNodes[1].childNodes[2].childNodes[2].attributes[0].nodeValue.match(/d=(\d+)/)[1]
	
	// tribe
	var firsttype = units.childNodes[1].childNodes[2].childNodes[0].attributes[0].nodeValue
	var t = "1";
	if(firsttype == "Clubswinger") {
		t = "2";
	}
	if(firsttype == "Phalanx") {
		t = "3";
	}
	
	// attacker troops/casualties
	var troops = units.childNodes[2]
	var casualties = units.childNodes[3]
	var a = "";
	var c = "";
	for(var i = 1; i <= 11 && i <= troops.childNodes.length - 1; i++) {
		a += troops.childNodes[i].innerHTML + "-";
		c += casualties.childNodes[i].innerHTML + "-";
	}
	
	// info lines
	var si = "";
	for(var i = 0; i < infos.childNodes.length; i++) {
		si += "&i" + i + "=" + encodeURI(infos.childNodes[i].childNodes[1].innerHTML.replace(/<.*?>/g,"").trim())
	}
	
	// date
	var d = encodeURI(document.getElementById("report_surround").childNodes[1].childNodes[3].childNodes[3].innerHTML.replace(/<.*?>|on |at | o'clock/g,"").trim());
	
	var params = "id=" + id + "&h=" + h + "&t=" + t + "&a=" + a + "&c=" + c + si + "&d=" + d + "&au=" + auid + "&av=" + avuid + "&du=" + duid + "&dv=" + dvuid;
	GM_xmlhttpRequest({
		method: 'POST',
		url: 'http://foo.bar.org/tr/report.php',
		headers: {
			'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
			'Accept': '*',
			'Content-type': 'application/x-www-form-urlencoded',
			'Content-length': params.length
		},
		data: params,
		onload: function(responseDetails) {
			//alert(responseDetails.responseText);
		}
	});
}
