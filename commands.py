import os
import sys
from flask import abort, Flask, jsonify, request
from mcstatus import MinecraftServer
import slack
import json
import yaml
from mcuuid.api import GetPlayerData



#Function to get the UUID based on username
def getUUID(username):
    username = GetPlayerData(username) #uses mcuuid to get short uuid
    uuid = username.uuid 
    fulluuid = uuid[:8] + "-" + uuid[8:12] + "-" + uuid[12:16] + "-" + uuid[16:20] + "-" + uuid[20:] #converts that to long uuid
    return fulluuid


def parse(username): #parses HackClubTools config
    yamlFile = yaml.load(open("./config.yml")) #Opens (symlinked) HackClubTools file
    jsondump = json.dumps(yamlFile, indent=4) 
    jsonfinal = json.loads(jsondump)
    names = (jsonfinal.get("chat")) #gets "chat" section of file
    nickname = (names.get(getUUID(username))) #check UUID against getUUID()
    final = nickname.get('nickname')
    return str(final)
            


def online(): #Checks for online players
    server = MinecraftServer.lookup(os.environ['SERVER'])
    server = server.status()
    if server.players.online == 0:
        return "No players online!"
    
    slackMessage = ""
    slackMessage += (str(server.players.online) + " out of " + str(server.players.max) + ":bust_in_silhouette: online:\n") #sends player count in slack
    
    for player in server.players.sample: #sends currently online players
        slackMessage += ("- " + parse(player.name) + ' [' + player.name + '] '"\n") 
    return slackMessage

app = Flask(__name__)

def request_valid(request): #checks for valid slack token / ID
    token_valid = request.form['token'] == os.environ['TOKEN']
    team_id_valid = request.form['team_id'] == os.environ['TEAM_ID']
    return token_valid and team_id_valid


@app.route('/players', methods=['POST']) #checking for POST from slack
def players():
    if not request_valid(request):
        print('NOTVALID')
        abort(400)

    return jsonify(
        response_type='in_channel', #response in channel, visible to everyone
        text=online(),
    )

