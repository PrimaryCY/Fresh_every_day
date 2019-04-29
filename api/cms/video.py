# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/14 20:34
import datetime

from rest_framework.filters import SearchFilter,OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.viewsets import ModelViewSet,RedisCacheModelViewSet
from apps.video.serializer import *
from apps.video.models import Banner,VideoCategory,VideoSPU,PromotionVideo
from utils.token import redis
from utils.util import CustomLimitOffsetPagination


class BannerViewSet(ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


class CMSVideoCategoryViewSet(RedisCacheModelViewSet):
    queryset = VideoCategory.objects.all()
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_fields = ('id', 'level')
    search_fields = ('name',)
    ordering_fields = ('update_time', 'create_time')
    redis = redis
    redis_result_key = redis_key = 'Category'
    serializer_class=VideoCategorySerializer

    def get_list_queryset(self):
        return self.get_queryset()

    def perform_destroy(self, instance):
        instance.get_descendants(include_self=True).update(is_active=False)

    class RedisMeta:
        model = VideoCategory
        redis_fields = ('id', 'parent_id', 'name', 'level', 'desc', 'is_active')

class CMSVideoSpuViewSet(ModelViewSet):
    filter_backends = (SearchFilter,DjangoFilterBackend,OrderingFilter)
    serializer_class = VideoSPUSerializer
    filter_fields = ('category',)
    search_fields = ('name',)
    ordering_fields = ('update_time', 'create_time')
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        return VideoSPU.objects.filter(department__in=self.request.dept_ids).all()

    def perform_destroy(self, instance):
        instance.videosku_set.all().update(is_active=False)
        super().perform_destroy(instance)


class CMSVideoSkuViewSet(ModelViewSet):
    serializer_class = CMSVideoSKUSerializer
    queryset = VideoSKU.objects.all()

    def get_object(self):
        obj=super().get_object()
        if obj.spu.department_id not in self.request.dept_ids:
            raise APIException({"error":"您没有查看权限"})
        return obj


class CMSPromotionVideoViewSet(ModelViewSet):
    serializer_class = CMSPromotionVideoSerializer

    def get_queryset(self):
        return PromotionVideo.get_queryset(self.request.dept_ids)

class CMSShowVideoViewSet(ModelViewSet):
    serializer_class = PostShowVideoSerializer
    lisy_queryset = VideoCategory.objects.filter(level=0)
    list_serializer=ListShowVideoSerializer
    queryset = ShowVideo.objects.all()
    def get_serializer_class(self):
        if self.action in {"list","retrieve"}:
            return self.list_serializer
        return self.serializer_class

    def get_queryset(self):
        if self.action in {"list","retrieve"}:
            return ShowVideo.get_queryset()
        return self.queryset

    def list(self, request,*args,**kwargs):
        data=super().list(request,*args,**kwargs)
        return Response(data=[dict for dict in data.data if dict['spu'].exists()],
                        status=data.status_code,headers=data._headers)

