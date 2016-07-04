#!/usr/bin/env python2

import time
import os
import datetime
import re
import subprocess
from slackclient import SlackClient

token = "xoxb-316470992"
bot_user = "U0XK12X63"

programsdir = '/home/smib/smib-commands/'
all_commands = {}
all_commands_time = 0

error_count = 0
users = {}
chans = {}

sc = SlackClient(token)

def get_commands_by_dir():
    #gah
    global all_commands_time, all_commands

    d = datetime.datetime.fromtimestamp(os.path.getmtime(programsdir))
    if all_commands_time == 0 or d > all_commands_time:
        for filename in os.listdir(programsdir):
            if os.path.isfile(programsdir + filename) and os.access(programsdir + filename, os.X_OK):
                match = re.search(r"(\w+).\w+", filename, re.MULTILINE)
                if match:
                    all_commands[match.group(1)] = programsdir + filename
                    #print programsdir + filename
        all_commands_time = d
    return

def get_command(command):
    global all_commands

    if command in all_commands:
        return command
    return False

    # todo: partial matches

if sc.rtm_connect():
    # initial poll of smib-commands
    get_commands_by_dir()
    
    # initial poll of users
    userslist = sc.api_call("users.list")
    for member in userslist['members']:
        users[member["id"]] = member["name"]
    
    chanslist = sc.api_call("channels.list")
    for channel in chanslist['channels']:
        chans[channel["id"]] = channel["name"]
    
    while True:
        try:
            new_evts = sc.rtm_read()
        except:
            if error_count > 10:
                raise
            error_count += 1
            continue
        
        error_count = 0
        for evt in new_evts:
            #print evt
            if "type" in evt:
                if evt["type"] == "message" and "text" in evt:
                    try:
                        match = re.search(r"^\?(\w+) {0,1}(.*)", evt["text"], re.MULTILINE)
                    except:
                        print evt
                        continue
                    if match:
                        sc.server.send_to_websocket({"type": "typing", "channel": evt["channel"], "id": 1})
                        get_commands_by_dir()
                        command = match.group(1).lower()
                        argline = match.group(2)
                        is_command = get_command(command)
                        if is_command == False:
                            sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text="Sorry, I don't have a "+command+" command.")
                            continue
                        script = all_commands[command]
                        os.chdir(programsdir)
                        
                        # Channel Messages
                        if evt["channel"][:1] == "C":
                            try:
                                p = subprocess.Popen([script, users[evt["user"]], chans[evt["channel"]], chans[evt["channel"]], argline], shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                                sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text=''.join(p.stdout.readlines()))
                            except:
                                sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text=command+" is on fire!")
                            
                        # Direct Messages
                        if evt["channel"][:1] == "D":
                            try:
                                p = subprocess.Popen([script, users[evt["user"]], 'null', evt["channel"], argline], shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                                sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text=''.join(p.stdout.readlines()))
                            except:
                                sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text=command+" is on fire!")
                            
                    time.sleep(1)
                    continue
                if evt["type"] == "user_change":
                    userslist = sc.api_call("users.list")
                    for member in userslist['members']:
                        users[member["id"]] = member["name"]
                    continue
                if evt["type"] == "channel_created" or evt["type"] == "channel_rename":
                    chanslist = sc.api_call("channels.list")
                    for channel in chanslist['channels']:
                        chans[channel["id"]] = channel["name"]
                
                    
        time.sleep(0.1)
else:
    print "Connection Failed, invalid token?"
