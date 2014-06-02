/*
The MIT License (MIT)

Copyright (c) 2014 Jianxia Xue xuejianxia@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

gssb.js 
- created by J.Xue -20140526-

Support:
- view messages from a speaker by clicking speaker name in both statistic and message area
- view messages in a particular type by clicking message type name in statistic area
- return to completed view from selected view by clicking the timestamp area, with the clicked message item at the top of the page
- view other chat records by clicking on a date from the jquery datepicker
- initiate speakerGraph objects corresponding to the daily/weekly/monthly speaker graph (SG) content
(the above function depends on the script of gssbSpeakerGraph.js)

*/
function messagesSelect( key, value ) {    
    $('div.message').hide();
    var selector = 'div.message['+key+'="'+value+'"]';
    $(selector).show();
}

function messageAll() {
    $('div.message').show();
}

function messageAllatAnchor( id ) {
    messageAll();
    location.href = "#"+id;
}
 
function load( date ) {
    var scriptName = "json/"+date+".json";
    console.log(scriptName);
    var loader = $.getScript(scriptName)
	.done(function(data, textStatus) {
	    console.log(textStatus);
	})
	.fail(function( jqxhr, settings, exception) {
	    console.log(jqxhr.status);
	});
    var loader = $.ajax({
	url: scriptName,
	type: 'get',
	error: function(data) {console.log(data);},
	success: function(data) {
	    console.log(data);
	}
    });
}

$(document).ready(function(){
    d = speakerGraphs;
    name = d.daily.label;

    var dp = $( "#datepicker" ).datepicker({
	showWeek: true, 
	firstDay: 1,
	dateFormat: "yy-mm-dd",
	defaultDate: name,
	nextText: '',
	prevText: '',
	onSelect: function(dateText){
	    var url = $(location).attr('href');
	    url = url.replace(name, dateText);
	    console.log(url);
	    window.open(url, "_self");
	}
    });
    
    $('span.speakerShow').click(function(){
	messagesSelect('speaker', $(this).html());
    });
    $('span.typeShow').click(function(){
	messagesSelect('msgtype', $(this).attr('msgtype'));
    });
    $('span.total').click(function(){
	messageAll();
    });
    $('div.timestamp').click(function(){
	messageAllatAnchor( $(this).parent().attr('id'));
    });

    var c = d3.select('.monthlySG');
    if (d.monthly !== null) {
	new SpeakerGraph(c, d.monthly);
    }
 
    c = d3.select('.weeklySG')
    if (d.weekly !== null) {
	new SpeakerGraph(c, d.weekly);
    }
    if (d.daily !== null)
	new SpeakerGraph(d3.select('.dailySG'), d.daily);

    
});
