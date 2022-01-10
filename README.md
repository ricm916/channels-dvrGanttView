# channels-dvrGanttView
A different way to look at your [channels-dvr](https://getchannels.com/) recording schedule.

This is now a simple Docker image setup, and it can be run on a different host than your channels-dvr machine.


Please don't run this on a public facing machine!, Use at your OWN RISK, etc, etc.



## Setup

Running the container is easy:

```
docker run -d --restart unless-stopped -p 8889:80 -e "TZ=America/Los_Angeles" -e channels=http://<<your channels-dvr ip address>>:8089 --name channels-dvr-gantt ricm916/channels-dvr-gantt
```
You will want to change the timezone parameter to match your region.  A list of timezones that "should" work can be found [HERE](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

You can also change the default screen refresh rate (60 seconds) by adding another environment variable:
```
docker run -d --restart unless-stopped -p 8889:80 -e "TZ=America/Los_Angeles" -e refresh=30 -e channels=http://<<your channels-dvr ip address>>:8089 --name channels-dvr-gantt ricm916/channels-dvr-gantt
```

You can see the recording schedule in your browser:

```
http://<<ip address of host>>:8889
```
## License
MIT
