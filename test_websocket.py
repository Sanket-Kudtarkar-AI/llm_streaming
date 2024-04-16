import json
import logging
import uuid

import pytz
from flask_cors import cross_origin
from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, emit
from llama_cpp import Llama
import eventlet
import requests
from flask_session import Session

logging.basicConfig(filename="./newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
sessionid_socketid_mapping = {}

IST = pytz.timezone('Asia/Kolkata')
rooms = {}
id_rooms = {}

llm = Llama(model_path='openchat-3.5-1210.Q5_K_M.gguf',
            n_gpu_layers=50,
            n_ctx=4096)


# HTTP Route handling
@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def handle_http():
    print(request.method, flush=True)
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "")
        response.headers.add('Access-Control-Allow-Methods', "GET,POST,OPTIONS")
        response.headers.add('Access-Control-Max-Age', '3600')
        return response

    if request.method == 'POST':
        response = {"response": "Connected. Awaiting socket connections."}
        return jsonify(response)
    else:
        return "This route only accepts POST requests with JSON data."


@socketio.on('connect')
def handle_connect():
    sessionidobtained = request.headers.get("sessionid")
    # print("Connected..",flush=True)
    if not sessionidobtained:
        pass
    else:
        requestfrom = request.headers.get("requestfrom")  # can be agent / client here.
        sessionid_socketid_mapping[sessionidobtained] = request.sid
        # Get corresponding RM id from API here
        if requestfrom:
            if requestfrom in ['client']:
                rmid = retrievermid(sessionidobtained)
                # Logic to create a room between customer and rm
                pass


@socketio.on('messagefromclient')
def handle_message(payload):
    payload = payload.json()
    print("message triggered", flush=True)
    query = payload["query"]

    sessionid = payload["sessionid"]
    messageid = str(uuid.uuid4())
    prompt_ = f'''GPT4 Correct User: {query}<|end_of_turn|>GPT4 Correct Assistant:'''
    for i in llm(prompt_, max_tokens=500, echo=True, temperature=0.0, stream=True):
        token = i['choices'][0]['text'].replace(prompt_, "")

        res = {"text": token,
               "sessionid": sessionid,
               "messageid": messageid,
               "query": query}

        emit('messagefromserver',
             res,
             broadcast=True,
             include_self=True)

        eventlet.sleep()


@socketio.on('disconnect')
def handle_disconnect():
    for k in sessionid_socketid_mapping.copy():
        if sessionid_socketid_mapping[k] == request.sid:
            del sessionid_socketid_mapping[k]


def retrievermid(sessionidobtained):
    return "8708213235"


import time


@app.route('/msg-to-flask', methods=['POST', 'GET'])
def incoming_msg():
    req = request.get_json()
    print(req)
    query = req['text']
    sessionid = req['sessionid']

    prompt_ = f'''GPT4 Correct User: {query}<|end_of_turn|>GPT4 Correct Assistant:'''
    res = {}
    for i in llm(prompt_, max_tokens=100, echo=True, temperature=0.0, stream=True):
        token = i['choices'][0]['text'].replace(prompt_, "")

        print(token)

        res = {"text": token,
               "sessionid": sessionid}

        # jsonify(res)
    requests.post(f"https://7eb6-103-173-124-200.ngrok-free.app/msg-to-node",
                  json=res)

    time.sleep(1)

    # res = jsonify(res)
    # return res


if __name__ == '__main__':
    socketio.run(app, port=3008, debug=False)
