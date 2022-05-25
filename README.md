# lab-mqtt

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
docker run -d --name emqx -p 11883:1883 -p 8081:8081 -p 8083:8083 -p 8084:8084 -p 8883:8883 -p 18083:18083 emqx/emqx:4.3.11
```

### 1.3 配置 MQTT 客户端

![](images/mqttx-config.png)

#### 1.3.1 MAC 上的 MQTTX

## 2. 压测

## 3. 消息共享
