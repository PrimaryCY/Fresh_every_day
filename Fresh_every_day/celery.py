# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 22:49
from celery import Celery
import os
import django
from django.conf import settings

# 为celery设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fresh_every_day.settings')
django.setup()
# 创建应用
app = Celery("Fresh_every_day.celery",broker='redis://192.168.187.132:6379/8')

# app.config_from_object('django.conf:settings')
# # 设置app自动加载任务
# # 从已经安装的app中查找任务
# app.autodiscover_tasks(settings.INSTALLED_APPS)

