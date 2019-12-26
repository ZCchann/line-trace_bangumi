# -*- coding: utf-8 -*-
from flask import Flask, request
import json
import requests
import base64
import hashlib
import hmac
from linebot import LineBotApi
from bangumi import tra_bangumi
import logging

#设置日志
logging.basicConfig(filename="./trace.log",format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#读取json文件内的参数
set = open("config.json",encoding='utf-8')
seting = json.load(set)
line_bot = seting["line_bot_Channel_access_token"]
line_bot_hannel = seting["line_bot_Channel_secret"]
domain = seting["server_domain"]
trace_moe_url = 'https://trace.moe/api/search?url='  #trace.moe的api地址
line_bot_api = LineBotApi(line_bot)

app = Flask(__name__)
line_bot_token = line_bot

number = [130] #trace.moe每24小时搜索上限 默认上限为150 除非你是开发者 建议设置150以内

@app.route("/trace_bangumi", methods=['POST'])
def bangumi():
    #验证部分
    #创建新频道 验证line webhook
    body = request.get_data(as_text=True)  # 接收传递来的信息
    channel_secret = line_bot_hannel  # Channel secret string
    hash = hmac.new(channel_secret.encode('utf-8'),
                    body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash)

    reply_url = "https://api.line.me/v2/bot/message/reply"
    reply = i["events"][0]["replyToken"]
    header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + "{" + line_bot_token + "}",
    }
    i = eval(body) #转换信息为字典
    if number[0] > 0:
        if i["events"][0]["message"]["type"] == "image":
            c = number[0] - 1  # 每发送一张图片 计数器-1
            number.clear()
            number.append(c)
            image_id = i["events"][0]["message"]["id"]
            message_content = line_bot_api.get_message_content(image_id) #从line服务器下载图片到本地服务器
            with open("/data/images/"+ image_id + ".jpg", 'wb') as fd:
                for chunk in message_content.iter_content():
                    fd.write(chunk)
            images_url = domain + image_id + ".jpg"
            trace_url = trace_moe_url + images_url
            requests.post(url=reply_url, data=json.dumps(tra_bangumi(trace_url,reply)), headers=header)
    elif number[0] == 0:
        vaule = "今日机器人搜索次数已达上限 请于24小时后再进行搜索"
        huifu = {
            "replyToken": reply,
            "messages": [{
                "type": "text",
                "text": vaule
            }]
        }
        requests.post(url=reply_url, data=json.dumps(huifu), headers=header)

    return 'OK'
if __name__ == "__main__":
    app.run(port='6000')