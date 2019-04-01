# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 22:54
from Fresh_every_day.celery import app

@app.task(name='xxxx')
def send_sms(SMS_CONF,mobile,code):
    check_sms = send_sms(SMS_CONF, mobile=mobile, user='用户', code=code, min='3分钟')
    res = check_sms.send_sms()
    return res
