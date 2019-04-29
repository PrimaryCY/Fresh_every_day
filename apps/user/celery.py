# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 22:54
from django.core.mail import EmailMultiAlternatives
from rest_framework.reverse import reverse

from Fresh_every_day.celery import app

from Fresh_every_day import settings
from utils.sms import Sms


@app.task
def send_sms(SMS_CONF,mobile,code):
    print('发送了短信')
    check_sms = Sms(SMS_CONF, mobile=mobile, user='用户', code=code, min='3分钟')
    res = check_sms.send_sms()
    return res

@app.task
def send_email(email,url):
    print('发送了邮件')
    msg = EmailMultiAlternatives(settings.EMAIL_SUBJECT,settings.EMAIL_CONTENT.format(url),
                                 settings.EMAIL_FROM, [email,])
    content=settings.EMAIL_HTML_CONTENT.format(url,url)
    msg.attach_alternative(content, "text/html")
    msg.send()
