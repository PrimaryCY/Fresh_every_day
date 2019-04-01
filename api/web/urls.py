# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 19:31
from django.conf.urls import url,include
from rest_framework.routers import DefaultRouter


router=DefaultRouter()

urlpatterns = [
    url(r'^',include(router.urls)),

]
