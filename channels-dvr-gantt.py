#!/usr/bin/env python3

import json
import time
import requests
import math
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs


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
        query_components = parse_qs(urlparse(self.path).query)
        if 'source' in query_components:
            source = query_components["source"][0]

        #print(parse_qs(urlparse(self.path).query)) #log the query string to console
        html = getHTML(source)

        # Writing the HTML contents with UTF-8
        self.wfile.write(bytes(html, "utf8"))
        jobs.clear()
        providers.clear()
        return

class job:
        def __init__(self,id,name,channel,start,duration):
                self.id = id
                self.name = name
                self.channel = channel
                self.start = start
                self.duration = duration
                self.provider = getProvider(channel)

class provider:
    def __init__(self,deviceID,FriendlyName,channels,color_num):
        self.id = deviceID
        self.name = FriendlyName
        self.channels = channels
        self.color = colors[color_num]
    def getColor(self,key):
        return [color for color in self if getattr(name == key)]

class channel:
    def __init__(self,id,guideNumber,guideName,station):
        self.id = id
        self.number = guideNumber
        self.name = guideName
        self.station = station

def getJobs(source="all"):
    jobs.clear()
    result = requests.get(channels_dvr + "dvr/jobs")
    data = result.json()
    for row in data:
        if (getProvider(row['Airing']['Channel']) == source) or (source == 'all'):
            jobs.append((row['Time'],job(row['ID'],row['Name'],row['Airing']['Channel'],row['Time'],row['Duration'])))

def getProviders():
    providers.clear()
    result = requests.get(channels_dvr + "devices")
    data = result.json()
    x = 0
    for row in data:
        chans = []
        for chan in row['Channels']:
            try:
                if not 'Hidden' in chan: # filter out hidden channels - there won't be anything scheduled to these
                    chans.append(channel(chan['ID'],chan['GuideNumber'],chan['GuideName'],chan['Station']))
            except:
                pass
        providers.append((row['FriendlyName'],provider(row['DeviceID'],row['FriendlyName'],chans, x)))
        x+=1

def getProvider(channel):
	for x,pro in providers:
		for chan in pro.channels:
			if str(chan.number) == str(channel):
				return(pro.name)
	 

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
<br />Updated: <b>"""+str(time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())))+"""</b><br /><br />
<form method="get" action="/"><select name="source" onchange="this.form.submit()">"""+selectors+"""</select>
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
            firststart_text = str(time.strftime('%Y-%m-%d %H:%M', time.localtime(firststart_adj)))
            lastend = jobs[-1][0] + jobs[-1][1].duration
            lastend_marker = lastend//(60 * 15) * (60 * 15) + (60 * 15)
            tot_time = math.ceil((lastend_marker-firststart_adj)/3600) #this is in hours!
            minutes_per_pixel = 60 # one minute per pixel graphing in seconds -- can be shortened here
            tot_width = tot_time * minutes_per_pixel

        selectors = ""
        if source == "all":
            selectors = "<option value=\"all\" SELECTED>All sources</option>"
        else:
            selectors = "<option value=\"all\">All sources</option>"
        
        for name in [name for name, ob in providers]:
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
                id=job.id
                name=job.name
                channel=job.channel
                provider=job.provider
                start=job.start//60
                duration=job.duration//60
                delay = start-(firststart_adj//60)
                HTML_BODY += """
<tr>
<td class="bar">
<table cellspacing="0" cellpadding="0" style="border: 0px;" width=\""""+str(tot_width)+"""px"><tr>
<td width=\""""+str(delay)+"""px\""""
                if x > len(jobs)/2:
                    HTML_BODY+=""" align="right"><b>"""+str(name)+"</b>&nbsp;(ch:"+str(channel)+","+str(provider)+") ("+str(duration)+" mins)&nbsp;</td>"
                else:
                    HTML_BODY+=">"
                
                HTML_BODY+="""
</td><td style="background-color: """+[p[1].color for p in providers if p[0] == provider][0]+""";" width=\""""+str(duration)+"""px" title=\""""+str(time.strftime('%m-%d-%Y %H:%M', time.localtime(start*60)))+""" - """+str(time.strftime('%H:%M', time.localtime(start*60+duration*60)))+"""\">
</td><td>"""
                if x <= len(jobs)/2:
                    HTML_BODY+="&nbsp;<b>"+str(name)+"</b>&nbsp;(ch:"+str(channel)+","+str(provider)+") ("+str(duration)+" mins)"
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
