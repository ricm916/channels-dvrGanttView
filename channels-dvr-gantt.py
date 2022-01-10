#!/usr/bin/python3

import sys
import os
import json
import time
import requests
import math
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
import cgi

#------------------------------------------------------------------
channels_dvr = os.environ.get('channels', 'http://localhost:8089/') # where to find channels-dvr server
if channels_dvr[-1] != "/": channels_dvr += "/"
PORT = 80 # port this will respond on
auto_refresh = str(os.environ.get('refresh', '60')) # number of seconds for html refresh meta tag
#------------------------------------------------------------------

jobs=[]
providers=[]

colors = [
    "#FF0000", #Red
    "#808080", #Gray
    "#0000FF", #Blue
    "#008000", #Green
    "#000080", #Navy
    "#00FFFF", #Cyan
    "#FF00FF", #Magenta
    "#800000", #Maroon
    "#808000", #Olive
    "#00FF00", #Lime
    "#FFFF00", #Yellow
    "#800080", #Purple
    "#008080", #Teal
]

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200) # Sending an '200 OK' response
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = getHTML('all')

            # Writing the HTML contents with UTF-8
            self.wfile.write(bytes(html, "utf8"))
            return
        else:
            if not self.path=="/favicon.ico":
                return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/":
            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

            self.send_response(200) # Sending an '200 OK' response
            self.send_header("Content-type", "text/html")
            self.end_headers()

            source=form['source'].value

            html = getHTML(source)

            # Writing the HTML contents with UTF-8
            self.wfile.write(bytes(html, "utf8"))
            return
        else:
            if not self.path=="/favicon.ico":
                return http.server.SimpleHTTPRequestHandler.do_GET(self)

class job:
    def __init__(self,name,channel,start,duration):
        self.name = name
        self.channel = channel
        self.start = start
        self.duration = duration
        self.provider = getProvider(channel)
        self.deviceid = getDeviceId(channel)
        self.endtime = start + duration

class provider:
    def __init__(self,deviceID,FriendlyName,channels,color_num):
        self.name = FriendlyName
        self.deviceid = deviceID
        self.channels = channels
        self.color = colors[color_num]

class channel:
    def __init__(self,guideNumber,guideName):
        self.number = guideNumber
        self.name = guideName

def getJson(url):
    return requests.get(url).json()

def getJobs(source="all"):
    jobs.clear()
    for row in getJson(channels_dvr + "dvr/jobs"):
        if ((getProvider(row['Airing']['Channel']) == source) or (source == 'all')) and not row['Skipped']:
            jobs.append((row['Time'],job(row['Name'],row['Airing']['Channel'],row['Time'],row['Duration'])))

def getProviders():
    providers.clear()
    x = 0
    for row in getJson(channels_dvr + "devices"):
        chans = []
        for chan in row['Channels']:
            try:
                if not 'Hidden' in chan: # filter out hidden channels - there won't be anything scheduled to these
                    chans.append(channel(chan['GuideNumber'],chan['GuideName']))
            except:
                pass
        providers.append((row['FriendlyName'],provider(row['DeviceID'],row['FriendlyName'],chans, x)))
        x+=1
    providers.sort()

def getProvider(channel):
	for x,pro in providers:
		for chan in pro.channels:
			if str(chan.number) == str(channel):
				return(pro.name)

def getDeviceId(channel):
	for x,pro in providers:
		for chan in pro.channels:
			if str(chan.number) == str(channel):
				return(pro.deviceid)

def formatTime(tm, fmt="%m-%d-%Y %H:%M"):
    return str(time.strftime(fmt, time.localtime(tm)))

def getColor(prv):
    try:
        return [p[1].color for p in providers if p[0] == prv][0]
    except:
        return "red"

def getHEAD(tot_width,selectors):
    HEAD="""
<html>
<meta http-equiv="refresh" content=\"""" + auto_refresh + """\" / >
<head>
<style>
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
    font-size: 1rem;
    font-weight: 400;
    line-height: 1;
    color: #212529;
    background-color: #fff;
    }
table {
  border: 0px;
  border-collapse: collapse;
  font-size: 0.75rem;
  font-weight: 500;
}
table td.bar {
    width: """ + str(tot_width) + """px;
    border: 0px;
}
img {
    height: 16px;
}
</style>
</head>
<body>
<form method="post" action="/"><select name="source" onchange="this.form.submit()">""" + selectors + """</select>
</form>"""
    return HEAD

def getHTML(source):
        getProviders()
        getJobs(source)
        tot_width = 0
        if len(jobs) > 0:
            jobs.sort(key=lambda x: x[0]) # sort list by start time
            firststart = jobs[0][0]
            if firststart > time.time(): # if no job running, use current time
                firststart = time.time()
            if len(jobs) < 20:
                firststart-=(3600*2)
            firststart_adj = firststart//(60 * 15) * (60 * 15) # round down to nearest 15 minute increment for the actual start time for the graph
            lastend = max([p[1].start + p[1].duration for p in jobs])
            lastend_marker = lastend//(60 * 15) * (60 * 15) + (60 * 15)
            tot_width = math.ceil((lastend_marker-firststart_adj)/60)
            if len(jobs) < 20:
                tot_width+=(60*3)
            now = int(time.time()//60-firststart_adj//60)

        selectors = ""
        if source == "all":
            selectors = "<option value=\"all\" SELECTED>All sources</option>"
        else:
            selectors = "<option value=\"all\">All sources</option>"

        for p in [p[1] for p in providers]:
            selectors += "<option value=\""+p.name+"\" "
            if p.name == source:
                selectors += " SELECTED"
            selectors+= ">"+p.name+"["+p.deviceid+"]"+"</option>"

        HTML_HEAD = getHEAD(tot_width,selectors)

        if len(jobs) > 0:
            HTML_BODY = """<table cellspacing="0" cellpadding="0" style="background: repeating-linear-gradient(90deg, #eee, 15px, #fff 15px, #fff 30px);">
<tr><td class="bar"><table cellspacing="0" cellpadding="0" style="border=0px;"><tr>
<td width=\"""" + str(now) + """px\"></td>
<td height="10px" width="1px" style="background-color:black;"></td>
<td>&nbsp;<b>""" + formatTime(time.time(),'%H:%M') + """</b></td>
</tr></table></td></tr>
"""
            x=0
            for start, job in jobs:
                x+=1
                name=job.name
                channel=job.channel
                provider=job.provider
                deviceid=job.deviceid
                start=job.start
                duration=job.duration//60
                delay = start//60-(firststart_adj//60)
                HTML_BODY += """
<tr>
  <td class="bar">
    <table cellspacing="0" cellpadding="0" style="border: 0px;" width=\"""" + str(tot_width) + """px">
      <tr>"""
                if (start > int(time.time())) and x < len(jobs)/2:
                    HTML_BODY+="""
                <td width=\"""" + str(delay) + """px\"><table width=\"""" + str(delay) + """px" cellspacing="0" cellpadding="0" style="border: 0px;" width=\"""" + \
                str(delay) + """px\">
<tr><td width=\"""" + str(now) + """px\"></td>
                <td width="1px" style="background-color:black;"></td>"""
                    if now <= delay - 1:
                        HTML_BODY+="<td width=\"""" + str(delay - now - 1) + """px\"><img src="/blank.gif" width=\""""+str(delay-now-1)+"""px\"/></td>"""
                    HTML_BODY += """
                </tr></table></td>"""

                else:
                    HTML_BODY+="""
        <td width=\""""+str(delay)+"""px\""""
                    if x > len(jobs)/2:
                        HTML_BODY+=""" align="right"><b>""" + name + "</b>&nbsp;(ch:" + str(channel) + "," + provider + ") (" + str(duration) + " mins)&nbsp;</td>"
                    else:
                        HTML_BODY+=">"

                HTML_BODY+="""</td><td style="background-color: """ + getColor(provider) + """;" width=\"""" + str(duration) + """px" title=\"""" + formatTime(start, '%a %B %-d, %Y %H:%M') + \
                """ - """ + formatTime(start+duration*60,'%H:%M') + """\"></td><td>"""
                if x <= len(jobs)/2:
                    HTML_BODY+="&nbsp;<b>" + name + "</b>&nbsp;(ch:" + str(channel) + "," + provider + " ["+deviceid+"]) (" + str(duration) + " mins)"

                HTML_BODY+="</td></tr><tr>"

                if x < len(jobs)/2:
                    HTML_BODY+="""<td colspan="3" style="height: 2px;"><table cellspacing="0" cellpadding="0" style="border: 0px;" width=\"""" + str(tot_width) + """px"><tr>
<td height="2px" width=\"""" + str(now) + """px\"></td><td height="2px" width="1px" style="background-color:black;"></td><td height="2px"></td></tr></table></td>"""
                else:
                    HTML_BODY+="""<td colspan="3" style="height: 2px;"></td>"""

                HTML_BODY+="</tr></table></td></tr>"

            HTML_BODY+="</table>"
        else:
            HTML_BODY = "No scheduled recordings found for " + source
        HTML_FOOTER = "</body></html>"

        return HTML_HEAD + HTML_BODY + HTML_FOOTER

def run():
	# setup and run the server:
	#------------------------------------------------------------------------
	socketserver.TCPServer.allow_reuse_address = True
	handler = MyHttpRequestHandler
	my_server = socketserver.TCPServer(("", PORT), handler)
	# Start the server
	my_server.serve_forever()

	#------------------------------------------------------------------------

if __name__ == '__main__':
	run()
