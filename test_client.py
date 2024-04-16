import socketio
import time

# Standard Python client
sio = socketio.Client()


@sio.event
def connect():
    print('Connection established')
    # Send a message right after connection
    prompt = "What is mutual funds?"
    sessionid = "abcde"
    data = {"query": prompt,
            "sessionid": sessionid}
    sio.emit('messagefromclient', data)


@sio.on('messagefromserver')
def response(data):
    print("'{}'".format(data["text"]))


@sio.event
def disconnect():
    print('Disconnected from server')

# sio.connect('http://localhost:3008')
sio.connect('https://repeatedly-pleasing-narwhal.ngrok-free.app')
# sio.connect('wss://f660-2409-40c0-102c-696-df7-6b7f-b7d1-8a2f.ngrok-free.app')


time.sleep(10)
sio.disconnect()
