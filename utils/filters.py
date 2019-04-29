# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/27 11:57
import re

from django_filters import rest_framework as FilterSet
from django.db.models import Q

from apps.video.models import OrderInfo

class PayStatusFilter(FilterSet.FilterSet):
    pay_status=FilterSet.CharFilter(method='get_pay_status')

    def get_pay_status(self,queryset,name,value):
        value=re.split(r',',value)
        return queryset.filter(pay_status__in=value)

    # class Meta:
    #     model=OrderInfo
    #     fields=('pay_status',)