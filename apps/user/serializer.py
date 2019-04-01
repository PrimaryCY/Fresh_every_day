# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 20:08
import re
from random import choice

from django.contrib.auth import get_user_model,authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from utils.token import token_ins
from utils.redis_desc import TokenRedisFunc,SmsRedisFunc
from utils.sms import SMS_CONF
from apps.user.celery import send_sms
from Fresh_every_day import settings

User=get_user_model()

class UserSerializer(serializers.ModelSerializer):
    signer_password=serializers.CharField(label='请重复输入密码',required=True,write_only=True)
    last_login=serializers.DateTimeField(read_only=True,label='最后登录时间')
    is_email=serializers.ReadOnlyField(label='是否邮箱验证')
    password=serializers.CharField(style={'input_type': 'password'},write_only=True,label='密码')

    def validate(self, attrs):
        if not attrs['signer_password']==attrs['password']:
            raise ValidationError('两次输入密码不一致')
        del attrs['signer_password']
        if re.match(settings.REGEX_MOBILE,attrs['username']):
            raise ValidationError('不可以使用手机号码作为用户名')
        return attrs


    class Meta:
        model=User
        exclude=('is_active',)


class LoginSerializer(serializers.Serializer):
    username=serializers.CharField(label='用户名',write_only=True)
    password=serializers.CharField(label='密码',write_only=True,required=False)
    code=serializers.CharField(label='验证码',write_only=True,required=False)
    user=serializers.ReadOnlyField()
    token=serializers.ReadOnlyField()
    token_ins=token_ins

    @property
    def username_field(self):
        try:
            self.modelssss = get_user_model()
            username_field = get_user_model().USERNAME_FIELD
        except:
            username_field = 'username'
        return username_field

    @TokenRedisFunc('user')
    def validate(self, attrs):
        user_input = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password'),
            'code':attrs.get('code')
        }
        if all({user_input.get(self.username_field),
                user_input.get('password')or user_input.get('code')}):
            user = authenticate(**user_input)

            if user:
                if not user.is_active:
                    raise serializers.ValidationError('登录失败,账户不存在')
                payload = self.token_ins.create_token_value(user)
                return {
                    'token': self.token_ins.generate_token(payload),
                    'username': user.username,
                }
            else:
                raise serializers.ValidationError('用户名或密码错误')
        else:
            raise serializers.ValidationError('请输入用户名和密码/验证码')


class SmsSerializer(serializers.Serializer):
    phone = serializers.CharField(label='手机号码', write_only=True,max_length=11,
                                  min_length=11,required=True,
                                  error_messages={'max_length': '手机号码过长',
                                                  'min_length': '手机号码过短',
                                                  'blank': '手机号码不能为空'})

    def validated_phone(self,phone):
        if not re.match(settings.REGEX_MOBILE, phone):
            raise ValidationError('请输入正确手机号码')
        return phone


    @SmsRedisFunc('user')
    def validate(self, attrs):
        mobile = attrs.get('phone')
        attrs['code'] = code = self.generate_code()
        # check_sms = send_sms(SMS_CONF, mobile=mobile, user='用户', code=code, min='3分钟')
        # res = check_sms.send_sms()
        send_sms.delay(SMS_CONF, mobile, code)
        return attrs

    def generate_code(self):
        seeds = "1234567890"
        random_str = []
        for i in range(4):
            random_str.append(choice(seeds))
        return "".join(random_str)