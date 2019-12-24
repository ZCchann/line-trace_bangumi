# -*- coding: utf-8 -*-
from flask import Flask, request
import json
import requests
import base64
import hashlib
import hmac
from linebot import LineBotApi

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

@app.route("/trace_bangumi", methods=['POST'])
def bangumi():
    #验证部分
    #创建新频道 验证line webhook
    body = request.get_data(as_text=True)  # 接收传递来的信息
    channel_secret = line_bot_hannel  # Channel secret string
    hash = hmac.new(channel_secret.encode('utf-8'),
                    body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash)
    i = eval(body) #转换信息为字典

    if i["events"][0]["message"]["type"] == "image":
        image_id = i["events"][0]["message"]["id"]

        message_content = line_bot_api.get_message_content(image_id) #从line服务器下载图片到本地服务器
        with open("/data/images/"+ image_id + ".jpg", 'wb') as fd:
            for chunk in message_content.iter_content():
                fd.write(chunk)
        images_url = domain + image_id + ".jpg"
        trace_url = trace_moe_url + images_url
        response = requests.get(trace_url)  # 获取trace.moe的返回信息
        response.encoding = 'utf-8'  # 把trace.moe的返回信息转码成utf-8
        result = response.json()  # 转换成dict格式
        animename = result["docs"][0]["title_chinese"]  # 切片番剧名称
        similarity = result["docs"][0]["similarity"]  # 切片相似度
        time = result["docs"][0]["at"]  # 切片时间
        episode = result["docs"][0]["episode"]  # 切片集数
        try:
            decimal = "." + str(similarity * 100).split('.')[1][:2]   #切片小数点后的内容 如果为空则不返回
        except IndexError:
            decimal = ""
        reply_url = "https://api.line.me/v2/bot/message/reply"
        reply = i["events"][0]["replyToken"]
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + "{" + line_bot_token + "}",
        }
        huifu = {
            "replyToken": reply,
            "messages": [{
                "type": "text",
                "text": "番剧名称：" + animename + " 第" + str(episode) + "集" + '\n'
                         "相似度：" + str(similarity * 100).split('.')[0] + decimal + "%"+  '\n'
                          + "时间：" + str(time / 60).split('.')[0] 
                         + '分' + str(time % 60).split('.')[0] + "秒"
            }]
        }
        requests.post(url=reply_url, data=json.dumps(huifu), headers=header)

    return 'OK'
if __name__ == "__main__":
    app.run(port='6000')