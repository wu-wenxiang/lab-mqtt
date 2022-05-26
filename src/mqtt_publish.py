import random
import sys
import time

from paho.mqtt import client as mqtt_client


if len(sys.argv) != 4:
    print(f'Usage: python {__file__} <broker> <port> <topic>')
    print(f'Example: python {__file__} broker.emqx.io 1883 "python/mqtt"')
    sys.exit(-1)

broker = sys.argv[1]
port = int(sys.argv[2])
topic = sys.argv[3]
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'


def connect_mqtt():
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


def publish(client):
    msg_count = 0
    while True:
        time.sleep(3)
        msg = f"[{time.time()}] {msg_count}"
        result = client.publish(topic, msg, qos=2, retain=True)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()
