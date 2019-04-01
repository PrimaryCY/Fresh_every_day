# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 21:44
from django.conf.urls import url,include
from rest_framework.routers import DefaultRouter

from api.cms.user import UserViewSet,LoginViewSet,SmsViewSet

router=DefaultRouter()
router.register('user',UserViewSet,base_name='user')
router.register('login',LoginViewSet,base_name='login')
router.register('sms',SmsViewSet,base_name='sms')

urlpatterns = [

    url(r'^',include(router.urls))
]
