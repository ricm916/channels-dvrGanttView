#!/usr/bin/env python3

import json
import time
import requests
import math
import http.server
import socketserver

# CHANGE THESE FOR YOUR CONFIGURATION
#--------------------------------------------
channels_dvr="http://<<your channels-dvr ip>>:8089/"
PORT = 8889
#--------------------------------------------

jobs=[]

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200) # Sending an '200 OK' response
        self.send_header("Content-type", "text/html")
        self.end_headers()

        #print(parse_qs(urlparse(self.path).query)) #log the query string to console
        html = getHTML()

        # Writing the HTML contents with UTF-8
        self.wfile.write(bytes(html, "utf8"))
        jobs.clear()
        return

class job:
        def __init__(self,id,name,channel,start,duration):
                self.id = id
                self.name = name
                self.channel = channel
                self.start = start
                self.duration = duration

def getJobs():
        result = requests.get(channels_dvr + "dvr/jobs")
        data = result.json()
        for row in data:
                jobs.append((row['Time'],job(row['ID'],row['Name'],row['Airing']['Channel'],row['Time'],row['Duration'])))

def getHTML():
        getJobs()
        jobs.sort(key=lambda x: x[0]) # sort list by start time
        firststart = jobs[0][0]
        firststart_adj = firststart//(60 * 15) * (60 * 15) # round down to nearest 15 minute increment for the actual start time for the graph
        firststart_text = str(time.strftime('%Y-%m-%d %H:%M', time.localtime(firststart_adj)))
        lastend = jobs[-1][0] + jobs[-1][1].duration
        lastend_marker = lastend//(60 * 15) * (60 * 15) + (60 * 15)
        lastend_marker_text = str(time.strftime('%Y-%m-%d %H:%M', time.localtime(lastend_marker)))
        tot_time = math.ceil((lastend_marker-firststart_adj)/3600) #this is in hours!
        minutes_per_pixel = 60 # one minute per pixel graphing in seconds -- can be shortened here
        tot_width = tot_time * minutes_per_pixel

        HTML_HEAD = """
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
    text-align: left;
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
<table cellspacing="0" cellpadding="0" style="background: repeating-linear-gradient(90deg, #eee, 15px, #fff 15px, #fff 30px);">
"""
        HTML_BODY = ""
        for start, job in jobs:
                id=job.id
                name=job.name
                channel=job.channel
                start=job.start//60
                duration=job.duration//60
                delay = start-(firststart_adj//60)
                HTML_BODY += """
<tr>
<td class="bar">
<table cellspacing="0" cellpadding="0" style="border: 0px;" width=\""""+str(tot_width)+"""px"><tr>
<td width=\""""+str(delay)+"""px"></td>
<td style="background-color: red;" width=\""""+str(duration)+"""px" title=\""""+str(time.strftime('%m-%d-%Y %H:%M', time.localtime(start*60)))+""" - """+str(time.strftime('%H:%M', time.localtime(start*60+duration*60)))+"""\">
</td>
<td>&nbsp;<b>"""+str(name)+"""</b>&nbsp;(ch:"""+str(channel)+""") ("""+str(duration)+""" mins)<!-- 
"""+str(time.strftime('%Y-%m-%d %H:%M', time.localtime(start*60)))+"""&nbsp;-&nbsp;"""+str(time.strftime('%Y-%m-%d %H:%M', time.localtime(start*60+duration*60)))+""" -->

</td>
</tr>
<tr><td colspan="3" style="height: 2px;"></td></tr>
</table></td>
</tr>
"""
        HTML_FOOTER = "</table></body></html>"

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
