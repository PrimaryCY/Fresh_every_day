# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 19:31
from django.conf.urls import url,include

from api.web.user import EmailViewSet,PersonalUserViewSet,UserAddrViewSet
from api.cms.user import LoginViewSet,SmsViewSet
from utils.routes import CustomRouter

router=CustomRouter()
router.register('login',LoginViewSet,base_name='login')
router.register('sms',SmsViewSet,base_name='sms')
router.register('email',EmailViewSet,base_name='email')
router.register('PersonalUser',PersonalUserViewSet,base_name='personaluser')
router.register('address',UserAddrViewSet,base_name='user_address')

urlpatterns = [
    url(r'web/',include(router.urls)),
]
