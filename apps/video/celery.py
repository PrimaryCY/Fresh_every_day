# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/31 22:54
from django.core.mail import EmailMultiAlternatives
from rest_framework.reverse import reverse

from Fresh_every_day.celery import app
from apps.video.models import PromotionVideo


@app.task
def delete_past_due(now):
    PromotionVideo.objects.filter(stop_date__lt=now).update(is_active=False)

