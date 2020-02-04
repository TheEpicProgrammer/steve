import json
import os
import sys
from uuid import UUID

import slack
from flask import Flask, abort, jsonify, request
from mcstatus import MinecraftServer
from mcuuid.api import GetPlayerData


#Function to get the UUID based on username
def getPlayerUUID(username):
    data = GetPlayerData(username) #uses mcuuid to get short uuid
    return UUID(data.uuid)

#new parse, supporting HCCore rather than HackClubTools
def getNickname(username):
    uuid = getPlayerUUID(username)
    with open (f"HCCore/players/{uuid}.json") as f:
        nick = json.load(f)['nickname']
        if nick == None: #if the Nick doesn't exist, return just the username
            nick = username
    return nick

def online(ver): #Checks for online players
    try:
        server = MinecraftServer.lookup(os.environ[f'{ver}'])
        server = server.status()
    except ConnectionRefusedError:
        return f"[{ver} Server] Server is down!"

    if server.players.online == 0:
        return f"[{ver} Server] No players online :disappointed:"

    slackMessage = ""
    slackMessage += (f"[{ver} Server] " + str(server.players.online) + " out of " + str(server.players.max) + ":bust_in_silhouette: online:\n") #sends player count in slack

    for player in server.players.sample: #sends currently online players
        nickname = getNickname(player.name)
        slackMessage += ("- " + nickname + ' [' + player.name + '] '"\n")

    return slackMessage

def concat():
    send = ""
    send = online('Modded') + "\n\n" + ("-" * 43) + "\n\n" + online('Vanilla') #adds spacing for slack

    return send

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

    print(request.values)
    return jsonify(
        response_type='in_channel', #response in chann  el, visible to everyone
        text=concat(),
    )
