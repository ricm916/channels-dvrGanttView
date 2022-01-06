#!/usr/bin/env python3

import json
import time
import requests
import math
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
import cgi


#--------------------------------------------------------------
#
# Notes:
#
# In general, more data is being captured into the classes
# than needed for future use. Low overhead to grab it,
# felt it was worth it for now.
#
#--------------------------------------------------------------


# CHANGE THESE FOR YOUR CONFIGURATION
#--------------------------------------------
channels_dvr="http://localhost:8089/"
PORT = 8889 # port this will respond on
#--------------------------------------------

jobs=[]
providers=[]

# re-order these however you want -- be sure to add more IF you have more than 13 sources...
colors = [
    "#FF0000", #Red
    "#808080", #Gray
    "#0000FF", #Blue
    "#00FF00", #Lime
    "#FFFF00", #Yellow
    "#00FFFF", #Cyan
    "#FF00FF", #Magenta
    "#800000", #Maroon
    "#808000", #Olive
    "#008000", #Green
    "#800080", #Purple
    "#008080", #Teal
    "#000080", #Navy
]

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200) # Sending an '200 OK' response
        self.send_header("Content-type", "text/html")
        self.end_headers()

        source = 'all'
        html = getHTML(source)

        # Writing the HTML contents with UTF-8
        self.wfile.write(bytes(html, "utf8"))
        return

    def do_POST(self):

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
        jobs.clear()
        providers.clear()
        return

class job:
    def __init__(self,name,channel,start,duration):
        self.name = name
        self.channel = channel
        self.start = start
        self.duration = duration
        self.provider = getProvider(channel)

class provider:
    def __init__(self,deviceID,FriendlyName,channels,color_num):
        self.name = FriendlyName
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
        if (getProvider(row['Airing']['Channel']) == source) or (source == 'all'):
            jobs.append((row['Time'],job(row['Name'],row['Airing']['Channel'],row['Time'],row['Duration'])))

def getProviders():
    providers.clear()
    x = 0
    for row in getJson(channels_dvr + "devices"):
        chans = []
        for chan in row['Channels']:
            #print(chan)
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
<meta http-equiv="refresh" content="300" / >
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
    width: """+str(tot_width)+"""px;
    border: 0px;
}
</style>
</head>
<body>
<br />Updated: <b>"""+formatTime(time.time())+"""</b><br /><br />
<form method="post" action="/"><select name="source" onchange="this.form.submit()">"""+selectors+"""</select>
</form>
"""
    return HEAD

def getHTML(source):
        getProviders()
        getJobs(source)
        tot_width = 0
        if len(jobs) > 0:
            jobs.sort(key=lambda x: x[0]) # sort list by start time
            firststart = jobs[0][0]
            firststart_adj = firststart//(60 * 15) * (60 * 15) # round down to nearest 15 minute increment for the actual start time for the graph
            lastend = jobs[-1][0] + jobs[-1][1].duration
            lastend_marker = lastend//(60 * 15) * (60 * 15) + (60 * 15)
            tot_width = math.ceil((lastend_marker-firststart_adj)/60)

        selectors = ""
        if source == "all":
            selectors = "<option value=\"all\" SELECTED>All sources</option>"
        else:
            selectors = "<option value=\"all\">All sources</option>"

        for name in [p[0] for p in providers]:
            selectors += "<option value=\""+name+"\" "
            if name == source:
                selectors += " SELECTED"
            selectors+= ">"+name+"</option>"        

        HTML_HEAD = getHEAD(tot_width,selectors)

        if len(jobs) > 0:
            HTML_BODY = "<table cellspacing=\"0\" cellpadding=\"0\" style=\"background: repeating-linear-gradient(90deg, #eee, 15px, #fff 15px, #fff 30px);\">"
            x=0
            for start, job in jobs:
                x+=1
                name=job.name
                channel=job.channel
                provider=job.provider
                start=job.start
                duration=job.duration//60
                delay = start//60-(firststart_adj//60)
                HTML_BODY += """
<tr>
<td class="bar">
<table cellspacing="0" cellpadding="0" style="border: 0px;" width=\""""+str(tot_width)+"""px"><tr>
<td width=\""""+str(delay)+"""px\""""
                if x > len(jobs)/2:
                    HTML_BODY+=""" align="right"><b>"""+name+"</b>&nbsp;(ch:"+str(channel)+","+provider+") ("+str(duration)+" mins)&nbsp;</td>"
                else:
                    HTML_BODY+=">"

                HTML_BODY+="""
</td><td style="background-color: """+getColor(provider)+""";" width=\""""+str(duration)+"""px" title=\""""+formatTime(start)+""" - """+formatTime(start+duration*60,'%H:%M')+"""\">
</td><td>"""
                if x <= len(jobs)/2:
                    HTML_BODY+="&nbsp;<b>"+name+"</b>&nbsp;(ch:"+str(channel)+","+provider+") ("+str(duration)+" mins)"
                HTML_BODY+="""
</td>
</tr>
<tr><td colspan="3" style="height: 2px;"></td></tr>
</table></td>
</tr>
"""
            HTML_BODY+="</table>"
        else:
            HTML_BODY = "No scheduled recordings found for " + source
        HTML_FOOTER = "</body></html>"

        return HTML_HEAD + HTML_BODY + HTML_FOOTER

# setup and run the server:
#------------------------------------------------------------------------
socketserver.TCPServer.allow_reuse_address = True
my_server = socketserver.TCPServer(("", PORT), MyHttpRequestHandler)
# Start the server
try:
    my_server.serve_forever()

except KeyboardInterrupt:
    print("ctrl-c detected... stopping server")
    my_server.shutdown()
#------------------------------------------------------------------------
