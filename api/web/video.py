# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/14 21:17
import re
from functools import reduce

from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import transaction

from api.viewsets import ReadOnlyModelViewSet,ModelViewSet,DestroyModelMixin,RetrieveModelMixin,CreateModelMixin
from apps.video.models import Banner,VideoCategory,VideoSPU,PromotionVideo,OrderInfo,VideoSKU
from apps.video.serializer import BannerSerializer,VideoSPUSerializer,IndexSerializer,\
    CMSVideoSKUSerializer,VideoSkuSerializer,OrderInfoSerializer
from Fresh_every_day.settings import COMMON_REDIS
from utils.redis_desc import RedisCache
from utils.token import redis
from api.cms.video import CMSVideoCategoryViewSet
from utils.util import sort_queryset,RedisTranscaction,CustomLimitOffsetPagination
from utils.filters import PayStatusFilter

User=get_user_model()
class WebBannerViewSet(ReadOnlyModelViewSet):
    """web的banner展示"""
    queryset = Banner.objects.order_by('index')
    serializer_class = BannerSerializer

    def get_queryset(self):
        return Banner.objects.filter(department__in=self.request.dept_ids).order_by('-created_time')

class WebVideoCategory(ReadOnlyModelViewSet):
    queryset = VideoCategory.objects.all()
    serializer_class = None
    redis = redis
    redis_result_key = redis_key = 'Category'

    @RedisCache(view_cls=CMSVideoCategoryViewSet)
    def list(self, request,*args,**kwargs):
        return super().list(request,*args,**kwargs)

    @RedisCache(view_cls=CMSVideoCategoryViewSet)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request,*args,**kwargs)

    def get_redis(self):
        return self.redis

    def get_list_queryset(self):
        return self.get_queryset()

    def get_redis_key(self):
        return self.redis_key

    def perform_destroy(self, instance):
        instance.get_descendants(include_self=True).update(is_active=False)

    class RedisMeta:
        model = VideoCategory
        redis_fields = ('id', 'parent_id', 'name', 'level', 'desc', 'is_active')

class WebVideoSPUViewSet(ReadOnlyModelViewSet):
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    filter_fields = ('category',)
    search_fields = ('name',)
    ordering_fields = ('update_time', 'create_time')
    serializer_class = VideoSPUSerializer

    def get_queryset(self):
        return VideoSPU.objects.filter(department__in=self.request.dept_ids).order_by('-created_time')

    def retrieve(self, request, *args, **kwargs):
        data=super().retrieve(request,*args,**kwargs)
        self.request._request.method='POST'
        BrowsingHistoryViewSet.as_view({'post':'create_extra'})(self.request._request,*args,**kwargs)
        return data


class IndexViewSet(ListModelMixin,GenericViewSet):
    """首页"""
    queryset=['index',]
    serializer_class = IndexSerializer

class BrowsingHistoryViewSet(ListModelMixin,GenericViewSet):
    """浏览记录"""
    redis=COMMON_REDIS
    serializer_class = VideoSPUSerializer

    @property
    def history_key(self):
        return f'history_{self.request.user.id}'

    def get_queryset(self):
        if self.redis.exists(self.history_key):
            sku_ids = self.redis.lrange(self.history_key, 0, 4)
            #queryset=reduce(lambda x,y:x|y,[VideoSKU.objects.filter(id=i) for i in sku_ids])
            return sort_queryset(VideoSKU,sku_ids)
        return []


    def create_extra(self,request,*args,**kwargs):
        instance_id=kwargs.pop('pk')
        if self.redis.exists(self.history_key):
            self.redis.lrem(self.history_key,0,instance_id)
        self.redis.lpush(self.history_key,instance_id)
        return Response(status=200,data={})

    def delete(self,request,*args,**kwargs):
        self.redis.delete(self.history_key)
        return Response(status=200,
                        data={'succeed':True,'msg':'清除成功'})


class ShoppingCartViewSet(ModelViewSet):
    serializer_class = VideoSkuSerializer
    redis=COMMON_REDIS

    def get_queryset(self):
        sku_ids=self.redis.hgetall(self.shopping_key)
        queryset=sort_queryset(VideoSKU,sku_ids.keys())
        for i in queryset:
            i.count=int(sku_ids.get(str(i.id)))
        return queryset

    @property
    def shopping_key(self):
        return f'shopping_{self.request.user.id}'

    def list(self, request, *args, **kwargs):
        data = super().list(request, *args, **kwargs)
        data.data_={}
        if data.data:
            data.data_['sku_amount']=reduce(lambda x,y:x+y,[data.data[i]['count'] for i in range(len(data.data))])
            data.data_['sku_num']=len(data.data)
            data.data_['data'] = data.data
        return Response(data=data.data_,
                        status=data.status_code, headers=data._headers)

    def create(self, request, *args, **kwargs):
        video = request.data.get('video')
        count = request.data.get('count')
        if not count.isnumeric():
            raise APIException({'error': '参数传递错误'})
        count = int(count)
        if not all([video, count]) or count<=0:
            raise APIException({'error': '参数传递错误'})

        obj=VideoSKU.objects.filter(id=video)
        if obj.exists():
            obj=obj.first()
            if count>obj.stock:
                raise APIException({'error':'库存不足'})
            self.redis.hset(self.shopping_key, video, count)
            return Response(data={'succeed': True, 'msg': '修改成功'}, status=200)
        raise APIException({'error':'商品不存在'})


    def delete(self,request,*args,**kwargs):
        ids=request.data.get('ids',None)
        ids=re.split(r',',ids)
        if ids:
            self.redis.hdel(*ids)
            return Response(data={'succeed': True, 'msg': '删除成功'}, status=200)
        raise APIException({'error':'参数类型传递错误'})


    def patch(self,request,*args,**kwargs):
        video = request.data.get('video')
        count = 1
        if not all([video, count]):
            raise APIException({'error': '参数传递错误'})

        video_obj = VideoSKU.objects.filter(id=video)
        if video_obj.exists():
            video_obj = video_obj.first()
            if video_obj.stock>0:
                old_count=0
                if self.redis.hexists(self.shopping_key,video):
                    old_count = int(self.redis.hget(self.shopping_key, video))
                if old_count:
                    old_count += 1
                    if old_count>video_obj.stock:
                        raise APIException({'error':'商品库存不足'})
                self.redis.hset(self.shopping_key, video, old_count or count)
                return Response(data={'succeed': True, 'msg': '修改成功'}, status=200)
            raise APIException({'error':'商品库存不足'})
        raise APIException({'error': '商品不存在'})


class OrderViewSet(ListModelMixin,CreateModelMixin,DestroyModelMixin,
                   RetrieveModelMixin,GenericViewSet):
    """web订单接口"""
    serializer_class = OrderInfoSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    search_fields = ('order_sn',)
    ordering_fields = ('update_time', 'create_time')
    pagination_class = CustomLimitOffsetPagination
    filterset_class = PayStatusFilter
    filterset_fields = ('pay_status',)

    def get_queryset(self):
        return OrderInfo.objects.filter(user=self.request.user).order_by('created_time')

    @transaction.atomic()
    def create(self, request, *args,**kwargs):
        return super().create(request,*args,**kwargs)

    @transaction.atomic()
    def perform_destroy(self, instance):
        """用户取消"""
        instance.pay_status="USER_CANCELLED"
        for order in instance.order_set.all():
            order.video.stock+=order.video_num
            order.video.save()
        instance.save()


class CMSOrderViewSet(ListModelMixin,DestroyModelMixin,RetrieveModelMixin,GenericViewSet):
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    filter_fields = ('pay_status',)
    search_fields = ('user__username',)
    ordering_fields = ('update_time', 'create_time')
    serializer_class = OrderInfoSerializer
    pagination_class = CustomLimitOffsetPagination
    filterset_class = PayStatusFilter
    filterset_fields = ('pay_status',)

    def get_queryset(self):
        user_lis=User.objects.filter(department__in=self.request.dept_ids).values_list('id',flat=True)
        return OrderInfo.objects.filter(user__in=user_lis).order_by('created_time')

    @transaction.atomic()
    def perform_destroy(self, instance):
        """后台取消"""
        instance.pay_status = "BACKGROUND_CANCEL"
        for order in instance.order_set.all():
            order.video.stock += order.video_num
            order.video.save()
        instance.save()


"""
后台修改密码
前端修改密码

修改支付状态
"""

