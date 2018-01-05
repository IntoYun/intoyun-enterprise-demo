#!/usr/bin/env python
# encoding: utf-8

import websocket 
import json
import requests 
import urllib

devId    = "YOUR_DEVICE_ID" # 订阅该设备的信息 
server   = '192.168.0.46:8080'       # 服务器地址 
httpUrl  = 'http://'+server
wsUrl    = "ws://"+server+"/websocket"
username = 'admin'
password = 'admin'
sessKey  = 'mySess'             # 和 configs/system.py 中的 "SESS_KEY" 值一致.  

# 消息类型编号
WIFI_INFO_CODE = 11
GW_INFO_CODE   = 12
LORA_INFO_CODE = 13
TCP_INFO_CODE  = 14
WIFI_RX_CODE   = 21
GW_RX_CODE     = 22
LORA_RX_CODE   = 23
TCP_RX_CODE    = 24

dpsInfo = dict()

def on_open(ws):
    d = json.dumps({"deviceId": devId})
    ws.send(d)

def on_close(ws):
    print "===> ws closed!!!"

def on_message(ws, message):
    # print "===> message: ", message
    msg = json.loads(message)
    # print "===> msg: ", msg
    prdId = msg['body']['prdId']
    print "===> original dps: ", msg['body']['data']
    newdata = restore_dps(prdId, msg['code'], msg['body']['data'])
    print "===> real dps    : ", newdata

def on_error(ws, error):
    print "===> error: ", error

    
def restore_dps(prdId, code, data):
    if (code==WIFI_RX_CODE)or(code==GW_RX_CODE)or(code==LORA_RX_CODE)or(code==TCP_RX_CODE):
        dps = request_dps(prdId)
        # print "===> original data: ", data
        for dpId, val in data.iteritems():
            dp = dps.get(int(dpId))
            if dp['type'] == 'float':
                dpmin = dp['min']
                dprelu = dp['resolution']
                if dprelu == '0':
                    realnum = val
                else:
                    realnum = val*1.0 / pow(10, int(dprelu)) 
                    data[dpId] = realnum
        return data
    else:
        return data

def request_dps(prdId):
    dps = dpsInfo.get(prdId, -1)
    if dps == -1:
        print "====> url: ", httpUrl
        authReq = requests.post(httpUrl+'/manager', {'username': username, 'password': password})
        cookies = dict({sessKey : authReq.cookies[sessKey]})
        prdReq  = requests.get(httpUrl+'/product/'+prdId, cookies=cookies)
        print "===> prdReq.content: ", prdReq.content
        prd = json.loads(prdReq.content)
        # print "===> get dps: ", prd['datapoints'] 
        newdps = reformat_dps(prd['datapoints'])
        dpsInfo[prdId] = newdps 
        return newdps 
    else:
        # print "===> cached dps: ", dps
        return dps

def reformat_dps(datapoints):
    newdps = dict()
    for dp in datapoints:
        newdps[dp['dpId']] = dp
    # print "==> newdps: ", newdps
    return newdps 
    
if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(wsUrl,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    print "===> ws: ", ws
    ws.on_open = on_open
    ws.run_forever()