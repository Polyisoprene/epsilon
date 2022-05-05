# epsilon

### 介绍

用于BiliBili直播及动态推送的nonebot2插件


### 安装教程

下载epsilon并将其放于nonebot的src/plugins目录内

### 使用说明

#### 1. 安装依赖

在有Requirment.txt的目录下打开控制台，并且输入

```python
pip install -r Requirment.txt
```

#### 2. 配置.env.prod

在nonebot的  **.env.prod**  配置文件内添加以下一行

```
COMMAND_START=["/"]
```

#### 3. 登录

配置好nonebot的超级用户后，使用超级用户在群内发送  ***/登录***   指令,之后使用 BiliBili APP扫描二维码登录

#### 4. 帮助

在群内发送 ***/帮助*** 查看帮助文档
