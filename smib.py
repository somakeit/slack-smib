import time
import os
import datetime
import re
import subprocess
from slackclient import SlackClient

token = "do_not_check_in"
bot_user = "U0XK12X63"

programsdir = '/home/smib/smib-commands/'
all_commands = {}
all_commands_time = 0

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
                    print programsdir + filename
        all_commands_time = d
    return

def get_command(command):
    global all_commands

    if command in all_commands:
        return command
    return False

    # todo: partial matches

if sc.rtm_connect():
    get_commands_by_dir()
    while True:
        new_evts = sc.rtm_read()
        for evt in new_evts:
            #print evt
            if "type" in evt and "user" in evt:
                if evt["type"] == "message" and evt["user"] != bot_user and "text" in evt:
                    match = re.search(r"^\?(\w+) {0,1}(.*)", evt["text"], re.MULTILINE)
                    if match:
                        sc.server.send_to_websocket({"type": "typing", "channel": str(evt["channel"]), "id": 1})
                        get_commands_by_dir()
                        command = match.group(1).lower()
                        argline = match.group(2)
                        is_command = get_command(command)
                        if is_command == False:
                            print sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text="Sorry, I don't have a "+command+" command.")
                            continue
                        script = all_commands[command]
                        os.chdir(programsdir)
                        p = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        print sc.api_call("chat.postMessage", as_user="false:", channel=evt["channel"], text=''.join(p.stdout.readlines()))
                    time.sleep(3)
else:
    print "Connection Failed, invalid token?"
