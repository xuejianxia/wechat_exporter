#!/usr/bin/env python
# encoding: utf-8
"""
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
"""

"""
extract chat record history and convert the data into webpages
author: Jianxia Xue
created: 20140521
#
# ===============preprocessing before running the script========================================
# Before running this script, you need to export the following files to a fixed file structure:
#   [I used iExplorer 3.2.3.5 on Mac OS X 10.7.5, exporting files from my iPhone 4 IOS 7.1]
# input file structure from iphone
#   Apps -> WeChat -> Documents -> A_Folder_with_Non_Zero_Hashcode -> 
#         DB/MM.sqlite
#         Audio/[chat_ID]/*
#         Img/[chat_ID]/*
#         OpenData/[chat_ID]/*
#         Video/[chat_ID]/*
#   Apps -> WeChat -> Library ->WechatPrivate -> emoticon1     ------------> emoticon1
#   
# ===============message types==================================================================
#  The messages can be in the type of text(including hyperlinks), image, audio, openfile(vidio, pdf, txt, etc)
#  Each type of message needs to be handled differently
#
#  For text type message, 

#      **select Type, count(*) from Chat_28228f7a9f1a43c84f9045374383c8a4 group by Type**
#      Type = 10000 (#92, system messages such as adding new member to group)
#             49 (#221,<msg><appmsg appid=""><title></title><url></url></appmsg></msg> hyperlink messages, with thumb image in OpenData)
#             48 (#9, ImgStatus = 1, Des = 1, <msg><location x="" y="" scale="" label""</location></msg>)
#             47 (#341, ImgStatus = 5/6, Des = 0/1, <emoji>)
#             43 (#12, ImgStatus = 1, Des = 1, <msg><videomsg/></msg>)
#             42 (#2, ImgStatus = 1, Des = 1, <?xml ?><msg></msg>)
#             34 (#177, ImgStatus = 7, Des = 1, <msg><voicemsg></msg>)
#             3  (#1646, ImgStatus = 2, Des = 1, <msg><img/></msg>)
#             1  (#51791, ) textual message, the original messages are recorded with one field comprised of 
#                           UsrName: actual_message  (from other users)
#                           or actural_message (from the owner of the local database)
#                           Status = 4 (messages not issued by the local owner)
#        this is useful to identify if there is a need to fetch external attachment files
#
#     Status = 2 (#3634)
#              3 (#263, ImgStatus=1, Type=1, Des=0)
#              4 (#50394)
#        this is useful to identify self vs. other speakers
#
#     ImgStatus = 1 (#51951)
#                 2 (#1820) not all ImgStatus 2 are in Type 3, the non-type-3 messages are in type-49
#                 5 (#6)
#                 6 (#337)
#                 7#16, 17#1, 21#108, 25#10, 42#29
#
#  Speaker graph:
#     speaker are in the order according to their counts of messages
#     in the adjancancy matrix, element[i][j] means speaker i appears within one minute after speaker j's last message
#
#  ==================Details of attached file types========================================================
#  For image type message (ImgStatus = 2, Type = 3, Des = 1), the local storage of the image is at 
#      DB/Img/chat_id/message_local_id.pic_thum, 
#      DB/Img/chat_id/message_local_id.pic, (the full version is only available is the message had been clicked (not confirmed yet) 
#      .pic can simply be renamed to .jpg to view
#   On Mac OS X 10.7.5, the following command converts all recursively
#   !!!!!!!! find . -iname "*.pic" -exec bash -c 'mv "$0" "${0%\.pic}.jpg"' {} \; !!!!!!!!
#   !!!!!!!! find . -iname "*.pic.thumb" -exec bash -c 'mv "$0" "${0%\.pic.thumb}.t.jpg"' {} \;  !!!!!!!!!
#  
#  The audio type message's local copies are stored at DB/Audio/chat_id/message_local_id.aud.
#      The .aud file format is the same as the amr file except that the header characters of #!AMR was excluded
#      the following link gives approach on how to convert aud to amr: http://bbs.feng.com/read-htm-tid-6261163.html
#
#  Downloaded a python script that converts aud to wav file, 
#      http://sourceforge.net/projects/audfilesconverter/files/aud%20converter/
#   the script uses the tool ffmpeg for the actual amr to wav conversion
#  Hence, need to install ffmpeg
#  brew cannot work, solution found from the following link:
#    http://superuser.com/questions/254843/cant-install-brew-formulae-correctly-permission-denied-in-usr-local-lib
#   "As of writing, Homebrew requires the contents of /usr/local to be chown'd to your username. This doesn't seem like a great solution, b#      ut it works, and is evidently the recommended use. See: https://github.com/mxcl/homebrew/issues/9953#issuecomment-3800557
#    You can do:
#      sudo chown -R `whoami` /usr/local
#   aud-converter.py is working
#    !!!audio messages can be heard.!!! 
#
#  There is a separate folder of DB/OpenData/chat_id/ which saves pdf, txt, mp4 files, as well as all the thumb images of the 
#      hyperlinks.
#==============================================================================================================================
#  The ideal outcome of the program is to eat a MM.sqlite file, along with three dedicated folders for images, audios, and additional 
#      files, and spits out a .html file containing the text chat records along with a folder containing 
#      the image, audio, and additional attachments to the main records
#  The program should accept record time range, so such exporting can be organized into monthly/weekly packages
#==============================================================================================================================
# 
# sqlite related reference: https://docs.python.org/2/library/sqlite3.html
"""
import sqlite3
import time, datetime, calendar
import sys, operator, glob, os.path
import xml.etree.ElementTree as ET
from lxml import etree
import codecs, json, inspect

"""
 Timestamp related conversions
"""
DailyTimestampStep = 24*3600;

def str2epoch( yyyy_mm_dd ):
    return int(time.mktime(datetime.datetime.strptime(yyyy_mm_dd,"%Y-%m-%d").timetuple()))

def epoch2str( timestamp ):
    return time.strftime('%Y-%m-%d', time.localtime(float(timestamp)))
# return the timestamp difference in munites
def minute_distance( tstamp1, tstamp2 ):
    d = datetime.timedelta(seconds = tstamp2-tstamp1)
    return d.minutes
# return true if the timestamp is on the first day of a month
def isMonthlyStart( timestamp ):
    t = time.localtime(float(timestamp));
    return t[2] == 1
# return true if the timestamp is on a Monday as the beginning of a week
def isWeeklyStart( timestamp ):
    t = time.localtime(float(timestamp));
    d = datetime.date(t[0], t[1], t[2])
    return d.isoweekday()==1
# return the timestamp of the begining of the following month from the given timestamp month
def nextMonth( timestamp ):
    t = time.localtime(float(timestamp));
    y = t[0]
    m = t[1]+1
    if m == 13:
        m = 1
        y += 1    
    return int(time.mktime([y, m, 1, 0, 0, 0, 0, 0, 0]))
# return the timestamp of the begining of the following week from the given timestamp week
def nextWeek( timestamp ):
    t = time.localtime(float(timestamp));
    y = t[0]
    d = datetime.date(t[0], t[1], t[2])
    diso = d.isocalendar()
    d1 = d-datetime.timedelta(days=(diso[2]-1))    
    d2 = d1+datetime.timedelta(weeks=1)
    return int(time.mktime(d2.timetuple()))
    

class Chat2HTML_EXPORTER:
    """
    The class that converts from weixin chat sqlite db to html
    """

    def __init__(self, dbFolder="DB_20140526/", htmlFolder = "html/", 
                 Chat_Table = 'Chat_28228f7a9f1a43c84f9045374383c8a4', # hardcoded now for gssb
                 dataProvider='xue', dataProviderID='wxid_mknhwpgccdz312', 
                 timestamp_bias=13*60*60, minute_thresh = 1):
        """
        Configuration including database file
        :param dbFolder: the input folder that contains the sqlite database and corresponding attachment data, imported from smart phone
        :param htmlFolder: the out folder that will contain the html files and their attachments
        
        :dataProvider: the name of the owner of the sqlite data
        :dataProviderID: the ID sequence of the data ownder, note that the infomation has be to digged manually

        :timestamp_bias: this bias will be added to the final presentation of the timestamp
        :minute_thresh: this is the minimum temporal difference between two speakers to be considered having real-time conversation
        """
        self.dbFolder = dbFolder
        self.htmlFolder =htmlFolder
        self.Chat_Table = Chat_Table;
        self.dataProvider = dataProvider
        self.dataProviderID = dataProviderID
        self.time_bias = timestamp_bias
        self.minute_thresh = minute_thresh # this is the maximum temporal distance to consider if any two speakers chat together
    
        # query related dyanmic data
        self.startTime = None
        self.stopTime = None
        self.queryName = None
        self.statType = 'user'
        # query results mathcing the above query data
        self.records = {};
        
        # query results that can contain multiply query statistics
        self.speakerGraphs = None
        self.stats = None

    """
    hard-coded input file and message structure
    """
    # hardcoded for the sqlite db file
    dbFile = 'DB/MM.sqlite';    
    # the manually decoded message types and their corresponding attachment file folder names hardcoded
    MsgType_Folder = {'49': 'OpenData', '47': 'emoticon1', '43': 'Video', '34': 'Audio', '3': 'Img'};
    MsgType_dict = {'10000': 'system notifications', '49': 'links', '48': 'locations',
                    '47': 'emotions', '43': 'videos', '42': 'xml', '34': 'audios', '3': 'images',
                    '1': 'texts'};

    """
    !!! All the following string templates are in the most naive form, 
    !!! the python template method was picky on the chinese characters.
    !!! Need fixing!
    """
    
    """
    hard-code database query patterns
    """
    # hardcoded column index
    Items = {'MsgLocalID': 1, 'CreateTime': 3, 'Message': 4, 'Status': 5, 'Type': 7};    
    # query strings with hard coded dependencies of MM.sqlite table names
    SQL_Templates = {
    "get_chatroom_name": '''select name from sqlite_sequence where seq = (select max(seq)  from sqlite_sequence)''',
    "check_friend_nickname": '''select NickName from Friend where UsrName == "%s"''',    
    "count_messages": '''select count(*) from %s where %s''',
    "get_messages": '''select * from %s where %s''',
    "get_messages_where": '''CreateTime >= %d and CreateTime < %d'''
    }
    
    """
    hard-coded output template
    """
    htmlTemplate = '''
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>GSSB WeChat Message Archive</title>
    <meta name="author" content="Jianxia Xue">
    <meta name="create date" content="%s">
    <link rel="stylesheet" type="text/css" href="style/gssb.css">
    <script type="text/javascript" src="js/jquery-1.11.1.min.js"></script>
    <script src="js/jquery-ui-1.10.4.custom.min.js"></script>
    <link rel="stylesheet" href="style/jquery-ui-1.10.4.custom.min.css">
    <script type="text/javascript" src="js/gssb.js"></script>    
    <script type="text/javascript" src="js/d3.v3.min.js"></script>
    <script src="js/gssbSpeakerGraph.js"></script>
    <script>
    speakerGraphs = %s;
    </script>

    </head>
    <body class="gssbWechatArchive">    
    %s
    </body>
    </html>
    '''
    
    archiveLeafTemplate = '''<div id="%s">
    <div id="datepicker"></div>    
    %s
    <div class="records">%s</div></div>    
    <div class="dailySG"></div>    
    <div class="monthlySG"></div>
    <div class="weeklySG"></div>
    '''
    
    statTemplate = '''
    <div class="stat" class="%s">
    <div class="queryName">%s</div>
    <div class="typeStat"><span class="total">%d Messages:</span> %s</div>
    <div class="speakerStat"><span class="total">from %d speakers:</span> %s</div>
    </div>
    '''
    
    typeStatTemplate = '''<div class="typeData">%d <span class="typeShow" msgtype="%s">%s</span></div>'''
    speakerStatTemplate = '''<div class="speakerData"><span class="speakerShow">%s</span> %d</div>'''

    messageTemplate = '''<div class="message" id="%s" speaker="%s" msgtype="%s"><div class="timestamp">%s</div><span class="speakerShow">%s</span><span class="content">%s</span></div>'''

    emojiMsgTemplate = '''<img height="80px" src="%s/%s.t.jpg" />'''
    unknownMsgTemplate = '''<span class="unknown">%s</span>'''
    linkMsgTemplate = '''<a href="%s">%s</a>'''
    link2MsgTemplate = '''<a href="%s"><div class="title">%s</div><div class="des">%s</div></a>'''
    audioMsgTemplate = '''<audio controls><source src="%s/%s.wav" type="audio/wav">
        Your brower does not support the audio element</audio>'''
    videoMsgTemplate = '''<video width="320" height="240" controls>
        <source src="%s/%s.mp4" type="video/mp4">
        Your browser does not support the video tag.
        </video>'''
    imgTagTemplate = '''<img src="%s.t.jpg" />'''
    imgMsgTemplate = '''<a href="%s.jpg">%s</a>'''
    locationURLTemplate = '''https://www.google.com/maps/@%s,%s,%sz'''
    
    def _initQueryStatistics(self):
        return {'monthly':None, 'weekly':None, 'daily':None, 'user':None};
    
    # collect message statistics
    def getMessageStat(self, cursor, timeClause):
        cur = cursor;
        cur.execute(self.SQL_Templates['count_messages'] % (self.Chat_Table, timeClause))
        data = cur.fetchone();
        self.messageTotal =  0 if data is None else data[0]

        stat = {}
        msgType = self.MsgType_dict
        for key, value in msgType.iteritems():
            cur.execute("select count(*) from %s where %s and Type==%s" % (self.Chat_Table, timeClause, key))
            data = cur.fetchone()
            stat[key] = 0 if data is None else data[0]
        self.messageStat = sorted(stat.iteritems(), key=operator.itemgetter(1), reverse=True);

    # collect speaker statistics
    def getSpeakerInfo(self, cursor, timeClause):
        cur = cursor;
        cur.execute( self.SQL_Templates['get_messages'] % (self.Chat_Table, timeClause))
        unlabeledSpeaker = self.dataProvider
        # build speaker dictionary
        speakers = {}
        for row in cur:
            msg = row[self.Items['Message']]            
            #parsing name
            parser = ':\n'
            idx = msg.find(parser)            
            speaker_id = unlabeledSpeaker if idx < 0 else msg[0:idx]
            speakers[speaker_id] = speakers.get(speaker_id,0)+1

        # build speaker activity sorted list
        speakerActivity = {};
        for key in speakers:
            cur.execute( self.SQL_Templates['check_friend_nickname'] % key);
            data = cur.fetchone()
            nickname = key if data is None else data[0]
            speakerActivity[nickname] = speakers[key]
            speakers[key] = nickname;            
        speakerActivity = sorted(speakerActivity.iteritems(), key=operator.itemgetter(1), reverse=True)
        self.speakers = speakers
        self.speakerStat = speakerActivity
    
    def _initSpeakerGraph(self):
        """
        the data structure will be exported to json format for the javascript
        to produce graph visualization of the speaker temporal viscosity measurement
        """
        nodes = []
        index = 0
        n = len(self.speakers)
        nameDict = {}
        for key, value in self.speakerStat:
            nodes.append({'name': key, 'r': value, 'lastT': -1000000, 'index': index});
            nameDict[key] = index
            index += 1
        links = [[0 for x in xrange(n)] for x in xrange(n)]
        self.speakerGraph = {"nodes": nodes, "links":links, "nameDict": nameDict}

    def _updateSpeakerGraph(self, speaker, timestamp):        
        nodes = self.speakerGraph['nodes']
        d = self.speakerGraph['nameDict']

        if not d.has_key(speaker):
            return None

        speakerIdx = d[speaker]
        speakerNode = nodes[speakerIdx]
        
        T = self.minute_thresh * 60

        for item in nodes:
            if item['name'] == speaker:
                continue

            node = nodes[d[item['name']]]

            if (timestamp - node['lastT'] ) < T:
                source = speakerNode['index']
                target = node['index']
                self.speakerGraph['links'][source][target] += 1
                
        self.speakerGraph['nodes'][speakerIdx]['lastT'] = timestamp
            
    def getMessages(self, cursor, timeClause):
        previousSpeaker = None
        previousTimestamp = 0
        previousType = -1

        T = 10*60;
        
        cur = cursor;
        record = []
        self._initSpeakerGraph()
        
        cur.execute( self.SQL_Templates['get_messages'] % (self.Chat_Table, timeClause))
        # marshall chat message record
        cnt = 0;
        for row in cur:
            msg = row[self.Items['Message']]         
            msgtype = row[self.Items['Type']]   
            #parsing name
            speaker,idx = self._parseSpeaker(msg, msgtype)
            #get message info
            msgid = row[self.Items['MsgLocalID']]
            timestamp = (int(row[self.Items['CreateTime']])+self.time_bias)
            #clean up message
            msg = msg[idx+1:].strip()
            msg = self.processMessage( msg, msgtype, msgid )
            timestep = timestamp-previousTimestamp;            
            self._updateSpeakerGraph(speaker, timestamp)
            # check if adjacent messages can be binded
            if (speaker == previousSpeaker and 
                timestep < T and 
                msgtype == previousType):
                record[-1][3] += "; "+msg
            else:
                if len(record)>0:
                    previousMsg = record[-1][3]
                else:
                    previousMsg = '' 
                previousSpeaker = speaker
                previousType = msgtype
                record.append([timestamp, speaker, msgtype, msg])
            previousTimestamp = timestamp
        self.records = record

    def _parseSpeaker(self, msg, msgtype):
        parser = ':\n'
        idx = msg.find(parser) 
        if idx < 0 :
            if msgtype == 48 or msgtype == 43:
                root = etree.fromstring( msg );
                node = root[0];
                d = node.attrib;
                speaker = d['fromusername']                
            elif msgtype > 1000:
                speaker = "system"
            else:
                speaker = self.dataProvider
        else:
            speaker = self.speakers[msg[0:idx]]
        return speaker, idx
    
    def processMessage(self, msg, msgtype, msgid):
        fDict = self.MsgType_Folder    
        folder = '' if not fDict.has_key(str(msgtype)) else fDict[str(msgtype)]
        if msgtype == 49:
            msg = self._process_appmsg(msg, msgid, folder)
        elif msgtype == 48:
            msg = self._process_location(msg)
        elif msgtype == 47:
            msg = self._process_emoji(msg, folder)
        elif msgtype == 43:
            msg = self._process_video(msgid, folder)
        elif msgtype == 34:
            msg = self._process_audio(msgid, folder)
        elif msgtype == 3:
            msg = self._process_img(msgid, folder)
        elif msgtype == 1:
            msg = self._process_text(msg)
        else:
            msg = self._process_others(msg)
        return msg

    def _process_emoji(self, msg, folder):
        #look for <msg><emoji md5="$1" /></msg>
        root = ET.fromstring( msg );
        node = root.find('emoji');
        if node is None:
            return self.unknownMsgTemplate % 'an unknown emotion'
        code = node.attrib["md5"];
        # then generate <img src="emoticon1/$1.jpg" />        
        return self.emojiMsgTemplate % (folder, code)

    def _process_location(self, msg):        
        #look for <msg><location x="$1" y="$2" scale="$3" label="$4" /></msg>
        root = etree.fromstring( msg );
        node = root.find('location');
        if node is None:
            return self.unknownMsgTemplate % 'an unknown location'

        # the hyperlink to produce <a href="https://www.google.com/maps/@$1,$2,$3z">$4</a>
        d = node.attrib;
        url = self.locationURLTemplate % (d['x'], d['y'], d['scale'])
        msg = self.linkMsgTemplate % (url, d['label'])
        return msg

    def _process_appmsg(self, msg, msgid, folder):
        #look for <msg><appmsg><type>$1</type><appmsg><msg> first
        root = etree.fromstring(msg)
        node = root.find('appmsg');
        if node is None:
            return '<span class="unknown">an unknown link</span'
        nodeType = node.find('type');
        title = node.find('title');
        # it is a OpenData file link, parse the <title>$2</title> content for the original filename
        if nodeType.text == '6':
            wildcard = '%s%s/%s.*' % (self.htmlFolder, folder, msgid)
            file = glob.glob( wildcard )
            if len(file) < 1:
                return self.unknownMsgTemplate % title.text
            #   and generate the hyperlink <a href="OpenData/$msgid.ext">original filename</a>
            name = file[0];
            name = name.replace(self.htmlFolder, '')
            return self.linkMsgTemplate % (name, title.text)
        else:
            # otherwise look for <msg><appmsg ><title>$2</title><des>$3</des><url>$4</url></appmsg></msg>
            des = node.find('des')
            url = node.find('url')
            #   and generate the hyperllink <a href="$4"><div class="title">$2</div><div class="des">$3</div></a>
            return self.link2MsgTemplate % (url.text, title.text, des.text)

    def _process_audio(self, msgid, folder):        
        return self.audioMsgTemplate % (folder, msgid)

    def _process_video(self, msgid, folder):
        return self.videoMsgTemplate % (folder, msgid)
        
    def _process_img(self, msgid, folder):
        filename = '%s/%s' % (folder, msgid)
        msg = self.imgTagTemplate % filename       
        file = glob.glob( 'html/%s.*' % filename )
        if len(file) > 1:
            msg = self.imgMsgTemplate % (filename, msg)
        return msg

    def _process_text(self, msg):        
        return msg.replace('\n', '<br />')

    def _process_others(self, msg):
        return msg

    TXTparser = '-------------------------------------------'
    def exportStatTXT(self):
        parset = self.TXTparser
        title = "Chat from %s to %s:" % (self.startTime, self.stopTime)
        msgStat = []
        for item in self.messageStat:
            if item[1] == 0:
                continue
            msgStat.append( '%d %s' % (item[1], self.MsgType_dict[item[0]]) )
        s1 = ", ".join(msgStat)
        speakerCount = "%d people attended" % len(self.speakers)
        speakerStat = []
        for item in self.speakerStat:
            speakerStat.append( "%s: %d" % (item[0], item[1]))
        s2 = "\n".join(speakerStat)
        return "\n".join( [parser, title, parser, speakerCount, 
                           parser, "Messages:"+s1, 
                           "Per speaker distribution: \n"+ s2, parser] )

    def exportRecordTXT(self):
        msg = [];
        for item in self.records:
            msg.append("%s: %s" % (item[1], item[3]));
        return "\n".join(msg)
    
    def exportStatHTML(self):
        tst = self.typeStatTemplate
        sst = self.speakerStatTemplate
        queryName = self.queryName
        
        typeStat = []
        for item in self.messageStat:            
            if item[1] == 0:
                continue
            typeStat.append(tst % (item[1], item[0], self.MsgType_dict[item[0]]))
        typeStat = '\n'.join(typeStat)
        
        speakerStat = []
        for item in self.speakerStat:
            item
            speakerStat.append(sst % (item[0], item[1]))
        speakerStat = '\n'.join(speakerStat);

        nt = self.messageTotal;
        ns = len(self.speakers)
        
        stat = self.statTemplate %(self.statType, queryName, nt, typeStat, ns, speakerStat)
        return stat

    def exportRecordHTML(self):
        mt = self.messageTemplate
        records = []
        for item in self.records:
            timestamp = item[0]
            timestr = datetime.datetime.fromtimestamp(timestamp)
            records.append( mt % (item[0], item[1], item[2], timestr, item[1], item[3]) )
        records = "\n".join(records)
        return records

    def exportArchiveHTML(self):
        stat = self.exportStatHTML()
        records = self.exportRecordHTML()
        archive = self.archiveLeafTemplate % (self.queryName, stat, records)
        return archive
    
    def exportHTML(self):
        if self.messageTotal < 1:
            return None
        archive = self.exportArchiveHTML()
        startTime = self.startTime
        stopTime = self.stopTime
        currentTime = time.strftime("%c")
        
        contents = self.htmlTemplate % (currentTime, json.dumps(self.speakerGraphs), archive)

        filename = '%s%s.html'%(self.htmlFolder,self.queryName)
        
        fid = codecs.open(filename, "w", encoding="utf-8")
        fid.write(contents)
        fid.close()
        print '...exported %s' % filename
        #webbrowser.open("file:///" + os.path.abspath(filename)) #elaborated for Mac

    def _ensembleStat(self):
        data = {'startTime': self.startTime, 'stopTime': self.stopTime, 
                'queryName': self.queryName,
                'messageStat': self.messageStat,
                'messageTotal': self.messageTotal,
                'speakerTotal': len(self.speakers),
                'speakerStat': self.speakerStat,
                'speakerGraph': self.speakerGraph};
        return data

    def exportArchiveJSON(self, filename):
        import json
        if len(self.records)<1:
            return False
        archive = self._ensembleStat()
        archive['record'] = self.records
        fid = codecs.open(filename, "w", encoding="utf-8")
        fid.write(json.dumps(archive));
        fid.close();
        return True

    def exportStatJSON(self, filename):
        import json
        if self.messageTotal<1:
            return False;
        stat = self._ensembleStat();
        fid = codecs.open(filename, "w", encoding="utf-8")
        fid.write(json.dumps(stat));
        fid.close();
        return True
    
    def _openDB(self):
        # connect db
        self.conn = sqlite3.connect(self.dbFolder+'/'+self.dbFile);
        self.cur = self.conn.cursor();

    def _closeDB(self):
        # close db
        self.conn.close()

    def _get_timeFrame_from_timestamp(self, a, b ):
        return self.SQL_Templates['get_messages_where'] % (a-self.time_bias, b-self.time_bias)
    
    def _get_timeFrame(self, startTime, stopTime):
        a = startTime
        b = stopTime
        if type(startTime) is str:
            a = str2epoch(a)
            b = str2epoch(b)
        return self._get_timeFrame_from_timestamp( a, b );
        
    # startTime and endTime must be in the string format of yyyy-mm-dd
    def loadData(self, startTime, stopTime, queryName):            
        self.startTime = startTime
        self.stopTime = stopTime
        self.queryName = queryName
        # the time limitation clause for all queries
        timeFrame = self._get_timeFrame(startTime, stopTime)
        self._openDB();
        self._queryData(timeFrame, self.cur)
        self._closeDB();

    def _queryData(self, timeFrame, cur):
        # collect statistic
        self.getMessageStat(cur, timeFrame)
        self.getSpeakerInfo(cur, timeFrame)
        # collect and process messages
        self.getMessages(cur, timeFrame)

    def _queryMonthly(self, timestamp):
        t = time.localtime(float(timestamp));
        nt = nextMonth(timestamp)
        self.startTime = epoch2str(timestamp);
        self.stopTime = epoch2str(nt)
        self.statType = "monthly"
        self.queryName = 'month%2d %s to %s' % (t[1], 
                                                self.startTime, 
                                                epoch2str(nt-1))
        # the time limitation clause for all queries
        timeFrame = self._get_timeFrame_from_timestamp(timestamp, nt)
        self._queryData(timeFrame, self.cur)
        self.speakerGraphs['monthly'] = self._ensembleSpeakerGraph()
        return t, nt
    
    def _queryWeekly(self, timestamp):
        nt = nextWeek(timestamp)
        t = time.localtime(timestamp)
        weekID = datetime.date(t[0], t[1], t[2]).isocalendar()[1]            

        self.startTime = epoch2str(timestamp);
        self.stopTime = epoch2str(nt);
        self.statType = "weekly"
        self.queryName = 'week%2d %s to %s' % (weekID, 
                                               self.startTime, 
                                               epoch2str(nt-1))
        # the time limitation clause for all queries
        timeFrame = self._get_timeFrame_from_timestamp(timestamp, nt)
        self._queryData(timeFrame, self.cur);
        self.speakerGraphs['weekly'] = self._ensembleSpeakerGraph()
        return t, nt, weekID
    
    def saveMonthlyStatJSON(self, startTime, stopTime):        
        print "from saveMonthlyStatJSON"
        timestamp = str2epoch(startTime)
        stopTimeStamp = str2epoch(stopTime)        
        self._openDB();
        while timestamp < stopTimeStamp:
            t, nt = self._queryMonthly(timestamp)
            filename = '%sjson/%.4d_month%.2d.json' % (self.htmlFolder, t[0], t[1])
            if self.exportStatJSON(filename):
                print "...%s, %d messages" % (self.queryName, self.messageTotal)
                print "...exported "+filename
            timestamp = nt
        self._closeDB();
        return None
        
    def saveWeeklyStatJSON(self, startTime, stopTime):
        print "from saveWeeklyStatJSON"
        timestamp = str2epoch(startTime)        
        stoTimeStamp = str2epoch(stopTime)        
        timestampStep = 7*DailyTimestampStep;
        self._openDB();
        while timestamp < stoTimeStamp:
            t, nt, weekID = self._queryWeekly(timestamp)
            filename = '%sjson/%.4d_week%.2d.json' % (self.htmlFolder, t[0], weekID)
            if self.exportStatJSON(filename):
                print "...%s, %d messages" % (self.queryName, self.messageTotal)
                print "...exported "+filename
            timestamp = nt
        self._closeDB();
        return None

    def _ensembleSpeakerGraph(self):
        nd = self.speakerGraph['nodes'];
        lk = self.speakerGraph['links'];

        nodes = []
        for item in nd:
            nodes.append({"name":item['name'], "r": item['r']})
        """    
        links = []
        for i in range(len(lk)):
            row = lk[i]
            for j in range(len(row)):
                if (row[j] > 0 ):
                    links.append({"source":i, "target":j, "value": row[j]})
        """            
        return {'nodes':nodes, "matrix": lk, "label": self.queryName}
    
    def saveSpeakerGraphJSON(self, filename):
        if self.messageTotal<1:
            return False;
        fid = codecs.open(filename, "w", encoding="utf-8")
        fid.write(json.dumps(self.speakerGraphs));
        fid.close();

    def _queryDaily(self, timestamp):
        nt = timestamp + DailyTimestampStep;
        self.startTime = epoch2str(timestamp);
        self.stopTime = epoch2str(nt);
        self.queryName = self.startTime
        self.statType = 'daily'
        # the time limitation clause for all queries
        timeFrame = self._get_timeFrame_from_timestamp(timestamp, nt)
        self._queryData(timeFrame, self.cur);
        self.speakerGraphs['daily'] = self._ensembleSpeakerGraph()
        return nt
        
    def saveDailyArchive(self, startTime, stopTime):
        print "from saveDailyArchiveJSON"
        timestamp = str2epoch(startTime)
        stoTimeStamp = str2epoch(stopTime)
        self._openDB();
        while timestamp < stoTimeStamp:
            self.speakerGraphs = self._initQueryStatistics();
            if isMonthlyStart(timestamp):
                self._queryMonthly(timestamp)
            if isWeeklyStart(timestamp):
                self._queryWeekly(timestamp)
            nt = self._queryDaily(timestamp)   
            self.exportHTML()
            timestamp = nt
        self._closeDB();
        return None
    
def main():
    narg = len(sys.argv);
    currentYear = time.strftime("%Y");
    startTime = currentYear+"-01-01";
    endTime = time.strftime("%Y-%m-%d")
    queryName = "this year till now"
    
    if narg >= 2:
        startTime = str(sys.argv[1])
    if narg >= 3:
        endTime = str(sys.argv[2])
    if narg >= 4:
        queryName = str(sys.argv[3])
        
        
    worker = Chat2HTML_EXPORTER()
    #worker.loadData( startTime, endTime, queryName, 'UserDefined' )
    #worker.exportHTML()
    worker.saveDailyArchive(startTime, endTime)
    #worker.saveWeeklyStatJSON(startTime, endTime)    
    #worker.saveMonthlyStatJSON(startTime, endTime)
    
if __name__ == "__main__":
    main()
