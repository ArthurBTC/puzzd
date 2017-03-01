from channels import Group
from channels.sessions import channel_session

from django.dispatch import receiver
import django.dispatch
from mainapp.signals import *


# Connected to websocket.connect
@channel_session
def ws_connect(message):
    # Accept connection
    message.reply_channel.send({"accept": True})
    # Work out room name from path (ignore slashes)
    room = message.content['path'].strip("/")
    # Save room in session and add us to the group
    message.channel_session['room'] = room
    Group("chat").add(message.reply_channel)

# Connected to websocket.receive
@channel_session
def ws_message(message):
    Group("chat").send({
        "text": message['text'],
    })

# Connected to websocket.disconnect
@channel_session
def ws_disconnect(message):
    Group("chat").discard(message.reply_channel)
    

@receiver(my_signal)
def ws_mysignal(sender, **kwargs):
    print("WS_MYSIGNAL")
    Group("chat").send({
        "text": 'YALA',
    })  

@receiver(beginSignal)
def ws_beginSignal(sender, **kwargs):
    print("WS_beginSignal")
    Group("chat").send({
        "text": 'beginSignal',
    })  

@receiver(stopSignal)
def ws_startSignal(sender, **kwargs):
    print("WS_stopSignal")
    Group("chat").send({
        "text": 'stopSignal',
    })    
    