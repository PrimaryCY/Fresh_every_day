# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 19:31
from django.conf.urls import include,url
from rest_framework.routers import DefaultRouter


urlpatterns = [
    url(r'web/',include(('api.web.urls','api.web'),namespace='web')),
    url(r'cms/',include(('api.cms.urls','api.cms'),namespace='cms')),
]
