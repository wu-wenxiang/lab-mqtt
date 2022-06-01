# lab-mqtt

Github: <https://github.com/wu-wenxiang/lab-mqtt>

Gitee 同步：<https://gitee.com/wu-wen-xiang/lab-mqtt>

## 1. 基本环境 Quick Start

### 1.1 基础环境

#### 1.1.1 云服务器：

- CentOS 7.9
- 2C/4G/40G
- 50M 带宽

#### 1.1.2 预配置

```console
$ pwd
/Users/wuwenxiang/local/github-mine/demotheworld/ansible

$ cat playbooks/cloudlab-init-with-rdp.yaml
- hosts: cloudlabs
  roles:
    # - init00-mount-disk
    - init01-prepare
    # - init02-rdp
    # - init03-01-kvm
  become: yes

$ diff inventory/lab-c2009.ini inventory/c2009.ini.example 
24c24,25
< lab-mqtt
---
> cloudlab001
> cloudlab002

$ ansible-playbook -i inventory/lab-c2009.ini playbooks/cloudlab-init-with-rdp.yaml
```

#### 1.1.3 安装 Docker 环境

参考：<https://gitee.com/dev-99cloud/training-kubernetes/blob/master/doc/class-01-Kubernetes-Administration.md#16-%E5%AE%9E%E9%AA%8Cdocker-quick-start>

```bash
apt-get update -y || yum update -y
apt-get install docker.io -y || yum install docker -y
systemctl enable docker --now
docker run hello-world
```

### 1.2 MQTT Server 搭建

#### 1.2.1 使用 emqx 搭建

```bash
# 搭建 MQTT Server（可选）
docker stop emqx
docker rm emqx
docker run -d --name emqx -p 1883:1883 -p 8081:8081 -p 8083:8083 -p 8084:8084 -p 8883:8883 -p 18083:18083 emqx/emqx:4.3.11
```

### 1.3 配置 MQTT 客户端

#### 1.3.1 MAC 上的 MQTTX

![](images/mqttx-config.png)

#### 1.3.2 Python Client

```bash
pip3 install paho-mqtt

python src/mqtt_subscribe.py 101.132.183.71 1883 "V2X.RSU.RSM.UP2"
python src/mqtt_publish.py 101.132.183.71 1883 "V2X.RSU.RSM.UP2"
```

### 1.4 MQTT 配置项

MQTT Spec：<https://mqtt.org/mqtt-specification/>

#### 1.4.1 QoS

按照 MQTT QoS 描述，QoS 2 表示 [Exactly once delivery](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718037)，QoS 2 需要服务端和客户端双方配合，参考 <https://www.emqx.com/en/blog/introduction-to-mqtt-qos>

![](images/mqtt-qos-0.webp)

![](images/mqtt-qos-1.webp)

![](images/mqtt-qos-2.webp)

| QoS of publish | QoS of subscribe | QoS of received message |
| - | - | - |
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 0 | 2 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |
| 1 | 2 | 1 |
| 2 | 0 | 0 |
| 2 | 1 | 1 |
| 2 | 2 | 2 |

测试场景：Wireshark 抓包（如果端口不是 1883，那么直接写 mqtt 过滤不出来，需要设置一下）

![](images/mqtt-wireshark-port-config.png)

一个 Publisher，三个 Subscriber

![](images/mqtt-qos-2-wireshark.png)

QoS 2 场景，Broker 只有在收到 PUBREC 才不再发 PUBLISH 消息，因此多 Subscribers 场景下，消息会发送多次（Message ID 不同）。

这里要考虑使用 MQTT 5.0 中的共享订阅，才能通过负载均衡来避免重复消息（也不能保证绝对）。

#### 1.4.2 Retain

Retain 的使用场景，参考 <https://www.emqx.com/en/blog/mqtt5-features-retain-message>

![](images/mqtt-retain.webp)

当 retain = True 时，发消息之后再 subscribe 对应 topic 的 client 也能收到，一般用于设备状态汇报。

#### 1.4.3 Clean Session

Clean Session 参考：<http://www.steves-internet-guide.com/mqtt-clean-sessions-example/>

Clean Session = False 时，除非 Client 主动 unsubsribe，否则 Topic 一直存在，离线消息会被保存，直至 client 重新上线接收，不论 QoS 0/1/2 均如此。

#### 1.4.4 结论

生产环境中，为了保证不丢包 & 兼顾性能

1. MQTT Version == 3.11 或 5？
2. CleanSession = True
3. Retain = False
4. QoS = 1

## 2. 压测

### 2.1 Jemeter

#### 2.1.1 Jmeter 测试 MQTT 服务

##### 2.1.1.1 前提条件

1. 已部署可在公网访问的 MQTT 服务
2. 已安装 JMeter 5.x 版本

##### 2.1.1.2 安装 MQTT Plugin

1. 下载 mqtt-jmeter 插件最新版本 JAR 包
2. 拷贝插件 JAR 包到 JMeter 安装目录的 lib/ext/ 子目录下

##### 2.1.1.3 本地编辑 Jmeter 脚本

打开 JMeter，新建脚本。右键单击 `Test Plan` ，选择 `Add > Threads (Users) > Thread Group`。右键单击 `Test Plan`，选择 `Add > Listener > View Results Tree`，添加 `View Results Tree` 监听器，方便本地调试测试脚本。

![](images/mqtt-jmeter-config.png)

##### 2.1.1.4 建立 MQTT 连接

建立 Subscribe 连接

首先建立与 MQTT 服务器之间的连接，并添加 MQTT Sub Sampler 订阅 MQTT 服务器。

![](images/mqtt-jmeter-subscribe.png)

右键单击 `Thread Group`，选择 `Add > Sampler > MQTT Connect`，配置如下：

![](images/mqtt-jmeter-connection.png)

MQTT 连接配置：

- Server name or IP 填写 腾讯MQTT 服务器公网地址。客户端设备通常使用公网访问 MQTT 服务。
- Port number MQTT 服务器端口。填写 21883。
- MQTT version 选择 MQTT 版本。选择 3.1.1，目前主流 MQTT 服务器都支持 3.1.1 版本。
- Timeout(s) 超时秒数填写，即客户端建立连接、发送消息等相关操作的超时时间。填写 10，可按需调整。
- Protocols 连接协议。选择 TCP，即使用标准 TCP 连接协议。
MQTT 客户端配置：
- User name 填写 emqx。
- Password 填写 public 。
- ClientId 填写 ${clientId}。（随意）
- 取消勾选 Add random suffix for ClientId 。本例使用预先准备好的固定客户端 ID，不要添加后缀。
- Keep alive(s) 活动心跳间隔秒数。填写 300，连接空闲时，每 5 分钟发送一次活动心跳，可按需调整。

##### 2.1.1.5 订阅消息

右键单击 `Thread Group`，选择 `Add > Sampler > MQTT Sub Sampler`，配置如下：

![](images/mqtt-jmeter-subscribe-message.png)

- QoS Level 服务器向客户端推送消息的服务质量。选择 1 ，即至少发送一次，可按需选择其他级别。
- Topic name 填写消息 topic 。应与发布消息的 topic 匹配。
- 勾选 Payload includes timestamp，与发送消息时添加时间戳对应，接收消息后从消息头解析出发送时间，从而计算出消息延迟，即从发布端、途经服务器、最后到达订阅端花费的总时间。
- Sample on 选择 specified elapsed time (ms)，值填写 1000，表示持续接收消息 1000 毫秒。
这段时间内，可能一条消息都接收不到，也可能接收到多条消息。
- 勾选 Debug response，记录接收到的消息内容，方便调试排查问题。正式执行性能测试时可取消该选项以优化性能和减少内存占用。

##### 2.1.1.6 建立 Publish 连接

建立与 MQTTOXY 服务之间的连接，并添加 MQTT Pub Sampler

MQTT 连接配置：

- Server name or IP 填写部署 MQTTOXY 服务的服务器公网地址。客户端设备通常使用公网访问 MQTT 服务。
- Port number MQTT 服务器端口。填写 5883。
- MQTT version 选择 MQTT 版本。选择 3.1.1，目前主流 MQTT 服务器都支持 3.1.1 版本。
- Timeout(s) 超时秒数填写，即客户端建立连接、发送消息等相关操作的超时时间。填写 10，可按需调整。
- Protocols 连接协议。选择 TCP，即使用标准 TCP 连接协议。
MQTT 客户端配置：
- User name 填写 emqx。
- Password 填写 public 。
- ClientId 填写 `${clientId}`。（随意）
- 取消勾选 Add random suffix for ClientId 。本例使用预先准备好的固定客户端 ID，不要添加后缀。
- Keep alive(s) 活动心跳间隔秒数。填写 300，连接空闲时，每 5 分钟发送一次活动心跳，可按需调整。

##### 2.1.1.7 发布消息

右键单击 Thread Group，选择 `Add > Sampler > MQTT Pub Sampler`，配置如下：

![](images/mqtt-jmeter-publish-message.png)

- QoS Level 客户端向服务器发布消息的服务质量。选择 1 ，即至少发送一次，可按需选择其他级别。
- Topic name 填写消息 topic 。MQTT topic 支持层次结构，使用 / 分割，类似文件路径，如 test_topic/test 等，这里简单使用 test_topic 做测试。
- 勾选 Add timestamp in payload ，消息头添加发送时间戳，方便测试时检查消息延迟。

#### 2.1.2 Jmeter 压测 MQ

创建测试脚本并添加线程组：创建两个脚本，一个用作消息发布，一个用作消息接受

1. 打开 JMeter，新建脚本。右键单击 Test Plan ，选择 `Add > Threads (Users) > Thread Group`

    ![](images/mqtt-jmeter-st-01.png)

2. 将两个脚本中的 Thread Group 分别重命名为 Publish Group 和 Subscribe Group

    ![](images/mqtt-jmeter-st-02.png)

    ![](images/mqtt-jmeter-st-03.png)

添加请求

1. 添加创建连接请求-分别选中 Publish Group 和 Subscribe Group，点击右键，`Add  > Sampler > MQTT Connect`

    ![](images/mqtt-jmeter-st-04.png)

2. 这个请求的作用是进行 MQTT 连接，ip 为 106.15.193.98，端口 1883，用户名 root， 密码 xxxx

    ![](images/mqtt-jmeter-st-05.png)

3. 由于连接操作每个线程中只有一次，因此 Publish Group 和 Subscribe Group 分别需要添加 Once Only Contoller ，然后将 MQTT Connect 拖入其下

    ![](images/mqtt-jmeter-st-06.png)

    ![](images/mqtt-jmeter-st-07.png)

4. 添加循环控制器 Loop Controller 选中 Publish Group 线程组，点击右键，`Add  > Logic Controller > Loop Controller`

    ![](images/mqtt-jmeter-st-08.png)

5. 该循环控制器的作用是设置循环发送消息的次数，这里设置为 2000

    ![](images/mqtt-jmeter-st-09.png)

6. 添加发布请求-选中 Loop Controller，点击右键，`Add  > Sampler > MQTT Pub Sampler`

    ![](images/mqtt-jmeter-st-10.png)

7. 该 MQTT 请求作用是发布消息到服务器，只需要输入主题、发送消息类型、发送消息内容即可

    ![](images/mqtt-jmeter-st-11.png)

8. 添加断开连接请求-选中 Publish Group 线程组，点击右键，`Add  > Sampler > MQTT Disconnect`

    ![](images/mqtt-jmeter-st-12.png)

9. 由于 Subscribe Group 需要保持监听，因此不设断开连接，需要将循环次数设为 Infinite

    ![](images/mqtt-jmeter-st-13.png)

10. 添加订阅请求-选中 Subscribe Group 线程组，点击右键，`Add > Sampler > MQTT Sub Sampler`

    ![](images/mqtt-jmeter-st-14.png)

11. 该请求作用是用来订阅发布的消息，只需要输入主题名称，即可订阅

    ![](images/mqtt-jmeter-st-15.png)

12. 分别为 Publish Group 和 Subscribe Group 添加观察结果树和聚合报告监听器，`Add  > Listener > View Results Tree / Aggregate Report`

    ![](images/mqtt-jmeter-st-16.png)

13. 在 Publish Group 中设置并发数为 200

    ![](images/mqtt-jmeter-st-17.png)

执行测试

1. 首先点击 Subscriber 的 Start 按钮，使之建立连接开始监听

    ![](images/mqtt-jmeter-st-18.png)

2. 再点击 Publisher 的 Start 按钮，开始发送消息

    ![](images/mqtt-jmeter-st-19.png)

测试结果

![](images/mqtt-jmeter-st-20.png)

### 2.2 代码压测

#### 2.2.1 python MQTT 类库

参考：<https://zhuanlan.zhihu.com/p/258782929>

Python MQTT 类库有三种：

1. <https://github.com/eclipse/paho.mqtt.python> 停更于 2021.10.21
1. <https://github.com/beerfactory/hbmqtt> 停更于 2020.04.11
1. <https://github.com/wialon/gmqtt> 停更于 2021.10.18

paho.mqtt.python 文档较全，为主流。

#### 2.2.2 paho + async

参考：<https://github.com/eclipse/paho.mqtt.python/blob/master/examples/loop_asyncio.py>

```python
#!/usr/bin/env python3

import asyncio
import socket
import uuid

import context  # Ensures paho is in PYTHONPATH

import paho.mqtt.client as mqtt

client_id = 'paho-mqtt-python/issue72/' + str(uuid.uuid4())
topic = client_id
print("Using client_id / topic: " + client_id)


class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        print("Socket opened")

        def cb():
            print("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        print("Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        print("Watching socket for writability.")

        def cb():
            print("Socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        print("Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        print("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        print("misc_loop finished")


class AsyncMqttExample:
    def __init__(self, loop):
        self.loop = loop

    def on_connect(self, client, userdata, flags, rc):
        print("Subscribing")
        client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        if not self.got_message:
            print("Got unexpected message: {}".format(msg.decode()))
        else:
            self.got_message.set_result(msg.payload)

    def on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)

    async def main(self):
        self.disconnected = self.loop.create_future()
        self.got_message = None

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        aioh = AsyncioHelper(self.loop, self.client)

        self.client.connect('mqtt.eclipseprojects.io', 1883, 60)
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

        for c in range(3):
            await asyncio.sleep(5)
            print("Publishing")
            self.got_message = self.loop.create_future()
            self.client.publish(topic, b'Hello' * 40000, qos=1)
            msg = await self.got_message
            print("Got response with {} bytes".format(len(msg)))
            self.got_message = None

        self.client.disconnect()
        print("Disconnected: {}".format(await self.disconnected))


print("Starting")
loop = asyncio.get_event_loop()
loop.run_until_complete(AsyncMqttExample(loop).main())
loop.close()
print("Finished")
```

这里用的是 `asyncio.get_event_loop`，[Get the current event loop. If there is no current event loop set in the current OS thread, the OS thread is main, and set_event_loop() has not yet been called, asyncio will create a new event loop and set it as the current one.Because this function has rather complex behavior (especially when custom event loop policies are in use), using the get_running_loop() function is preferred to get_event_loop() in coroutines and callbacks. Consider also using the asyncio.run() function instead of using lower level functions to manually create and close an event loop. Deprecated since version 3.10: Deprecation warning is emitted if there is no running event loop. In future Python releases, this function will be an alias of get_running_loop().](https://docs.python.org/3/library/asyncio-eventloop.html)，应该用 `get_running_loop` 或者 `asyncio.run()`。

get_running_loop: [Return the running event loop in the current OS thread. If there is no running event loop a RuntimeError is raised. This function can only be called from a coroutine or a callback.](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_running_loop) New in version 3.7

注意！python 3.6 在 2021.12 停止支持

[Run until the future (an instance of Future) has completed. If the argument is a coroutine object it is implicitly scheduled to run as a asyncio.Task. Return the Future’s result or raise its exception.](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_until_complete)

#### 2.2.3 异步服务

1. 非常基础的同步和异步编程入门介绍：[Getting Started With Async Features in Python](https://realpython.com/python-async-features/)
1. [Async IO in Python: A Complete Walkthrough](https://realpython.com/async-io-python/)
1. 参考 [mode](https://mode.readthedocs.io/en/latest/introduction.html)，去掉 `ensure_future` 和 `asyncio.get_event_loop` <http://github.com/ask/mode>

## 3. 消息共享
