# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/29 10:24
import os

from Fresh_every_day.settings import BASE_DIR


SMS_CONF={'data':"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <SendMessage3 xmlns="http://openmas.chinamobile.com/sms">
                    <destinationAddresses xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays"
                                          xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                        <a:string>{mobile}</a:string>
                    </destinationAddresses>
                    <message>【我的私人项目】亲爱的{user}，您的验证码是{code}。有效期为{min}，请尽快验证</message>
                    <extendCode>5</extendCode>
                    <applicationId>zzb3</applicationId>
                    <password>VBunGt5VLv4V</password>
                </SendMessage3>
            </s:Body>
        </s:Envelope>
        """,
        'url':'http://111.1.18.21:9080/OpenMasService',
        'headers':{
              'Content-Type': 'text/xml',
              'SOAPAction': 'http://openmas.chinamobile.com/sms/ISms/SendMessage3'
                    }
        }
SMS_EXPIRS=120

#公钥
PUL_KEY=os.path.join(BASE_DIR,'alipay','pul_key')
#私钥
PRIVATE_KEY=os.path.join(BASE_DIR,'alipay','private_key')
#阿里公钥
ALI_PUL_KEY=os.path.join(BASE_DIR,'alipay','alipay_key.txt')
