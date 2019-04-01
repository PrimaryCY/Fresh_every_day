# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 21:56
import requests

from django.utils.encoding import force_bytes

from Fresh_every_day.settings import SMS_CONF

class send_sms(object):

    def __init__(self, SMS_CONF,*args,**kwargs):
        """发送短信验证码"""
        self.SMS_CONF=SMS_CONF
        self.single_send_url = SMS_CONF['url']
        self.data=str(str(SMS_CONF['data']).format(**kwargs)).encode('utf-8')

    def send_sms(self):
        """
        发送验证码
        :param code: 验证码
        :param mobile: 手机号
        :return: 结果信息，dict类型
        """

        response = requests.post(url=self.single_send_url,
                                 data=self.data,
                                 headers=SMS_CONF.get('headers',''))
        return response

    @staticmethod
    def get_sms_redis_key(user_info):
        key = user_info.get('phone')
        return force_bytes(':'.join((key, 'code')))

