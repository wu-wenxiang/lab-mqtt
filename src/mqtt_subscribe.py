import random
import sys
from paho.mqtt import client as mqtt_client


if len(sys.argv) != 4:
    print(f'Usage: python {__file__} <broker> <port> <topic>')
    print(f'Example: python {__file__} broker.emqx.io 1883 "python/mqtt"')
    sys.exit(-1)

broker = sys.argv[1]
port = int(sys.argv[2])
topic = sys.argv[3]
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
# username = 'emqx'
# password = 'public'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `dup={msg.dup} mid={msg.mid} {msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic, 2)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
