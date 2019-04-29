import os

from celery import Celery
import django


# 为celery设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fresh_every_day.settings')
django.setup()
# 创建应用
app = Celery("Fresh_every_day.celery")
# 从django.conf:settings中加载celery配置
app.config_from_object('django.conf:settings')
# 设置celery从settings.INSTALLED_APPS中查找任务
from Fresh_every_day import settings
app.autodiscover_tasks(settings.INSTALLED_APPS)

#celery -A Fresh_every_day.celery worker -l info --pool=eventlet