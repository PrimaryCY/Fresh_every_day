# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/4/14 20:36
import re
import uuid
from functools import reduce

from django.forms.models import model_to_dict
from django.db.models.functions import Lower
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from apps.video.models import *
from utils.util import CustomChoiceFiled
from Fresh_every_day.settings import COMMON_REDIS,PRIVATE_KEY,PUL_KEY
from apps.user.serializer import UserAddrSerializer
from alipay.alipay import AliPay


class BannerSerializer(serializers.ModelSerializer):
    create_user=serializers.HiddenField(default=serializers.CurrentUserDefault(),
                                        label='创建人',write_only=False)
    user=serializers.ReadOnlyField(source='create_user.username')
    is_active=serializers.HiddenField(default=True,label='激活状态')
    index=serializers.IntegerField(min_value=0,label='轮播顺序')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.context['request'].method=='GET':
            self.fields['resource_data']=serializers.SerializerMethodField()
            self.fields.pop('table_name')
            self.fields.pop('table_id')

    def get_resource_data(self,obj):
        print(obj.content_obj)
        if obj.content_obj:
            return model_to_dict(obj.content_obj)
        return '无'

    class Meta:
        model=Banner
        fields="__all__"

class VideoCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model=VideoCategory
        exclude=('is_active','lft','rght','tree_id')

class VideoSPUSerializer(serializers.ModelSerializer):

    category=serializers.CharField(read_only=True)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        dept=Department.objects.filter(id__in=self.context['request'].dept_ids,is_active=True).all()
        self.fields['department']=serializers.PrimaryKeyRelatedField(queryset=dept,label='所属',
                                                                     source='department.name')

        #self.fields['department']=serializers.HyperlinkedRelatedField('cms:department-detail',read_only=True)
        #print(reverse('cms:email-list', request=self.context['request']))

        if self.context['view'].action !='list':
            self.fields['sku']=serializers.SerializerMethodField(label='sku数据')

    def get_sku(self,obj):
        return obj.videosku_set.filter(is_active=True).values()

    class Meta:
        model=VideoSPU
        exclude=('is_active',)


class CMSVideoSKUSerializer(serializers.ModelSerializer):
    specification=CustomChoiceFiled(choices=VideoSKU.VIDEO_SPCIFICATION,label='规格')
    spu=serializers.CharField(label='视频名称')
    is_active=serializers.ReadOnlyField(label='是否激活')


    class Meta:
        model=VideoSKU
        fields="__all__"

class CMSPromotionVideoSerializer(serializers.ModelSerializer):

    is_active=serializers.ReadOnlyField(label='是否激活')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if hasattr(self.context['request'],'dept_ids'):
            dept_ids=self.context['request'].dept_ids
            self.fields['department']=serializers.PrimaryKeyRelatedField(
                queryset=Department.objects.filter(id__in=dept_ids).all(),source='department.name',label='所属部门')
            self.fields['spu']=serializers.HyperlinkedRelatedField('cms:web-video-spu-detail',queryset=VideoSPU.objects.filter(department__in=dept_ids))

    class Meta:
        model=PromotionVideo
        fields="__all__"

class ListShowVideoSerializer(serializers.ModelSerializer):
    spu=serializers.SerializerMethodField(label='视频信息')

    def get_spu(self,obj):

        return obj.showvideo_set.filter(department__in=self.context['request'].dept_ids).values('spu_id','show_way',spu__category=Lower("category__name"),
                                    spu__name=Lower('spu__name'),spu__department=Lower("department__name"))

    class Meta:
        model=VideoCategory
        fields=("name",'spu')

class PostShowVideoSerializer(serializers.ModelSerializer):
    spu=serializers.CharField(label='视频信息')

    def validate(self, attrs):
        obj=VideoSPU.objects.filter(id=int(attrs.get('spu')))
        if obj.exists():
            ancestor_cate=obj.first().category.tree_id
            if ancestor_cate == attrs.get('category').id:
                attrs['spu']=obj.first()
                return attrs
            raise ValidationError({"error":'分类下无该视频'})
        raise ValidationError({"error":'无此视频'})

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if hasattr(self.context['request'],'dept_ids'):
            dept_ids=self.context['request'].dept_ids
            self.fields['department']=serializers.PrimaryKeyRelatedField(
                queryset=Department.objects.filter(id__in=dept_ids).all(),label='所属部门')

    class Meta:
        model=ShowVideo
        exclude=('is_active','created_time','update_time')


class IndexSerializer(serializers.Serializer):
    banner=serializers.SerializerMethodField(label='首页轮播图')
    promotionvideo=serializers.SerializerMethodField(label='首页促销')
    showvideo=serializers.SerializerMethodField(label='首页展示')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if not hasattr(self.context['request'],'dept_ids'):
            self.fields.clear()
        self.dept_ids=self.context['request'].dept_ids
        self.limit=3

    def get_banner(self,obj):
        return Banner.get_web_banners(self.dept_ids,self.limit,self.context)

    def get_promotionvideo(self,obj):
        return PromotionVideo.get_promotionvideo(self.dept_ids, self.limit, self.context)

    def get_showvideo(self,obj):
        return ShowVideo.get_showvideo(self.limit, self.context)


class VideoSkuSerializer(serializers.ModelSerializer):
    count=serializers.ReadOnlyField()

    class Meta:
        model=VideoSKU
        exclude=('is_active',)



class OrderInfoSerializer(serializers.ModelSerializer):
    user=serializers.HiddenField(default=serializers.CurrentUserDefault())
    video_ids=serializers.CharField(write_only=True,label='购物车选中视频列表')
    add_time = serializers.DateTimeField(read_only=True)
    pay_status = serializers.CharField(read_only=True)
    order_sn = serializers.CharField(read_only=True)
    trade_no = serializers.CharField(read_only=True)
    alipay_url = serializers.SerializerMethodField(label='支付宝链接')

    redis=COMMON_REDIS

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if  hasattr(self.context['request'],'dept_ids'):
            self.fields['address']=serializers.PrimaryKeyRelatedField(
                queryset=UserAddress.objects.filter(user=self.context['request'].user),label='邮寄地址',write_only=True)
            if self.context['view'].action =='retrieve':
                self.fields['address']=UserAddrSerializer(many=False,context=self.context,label='收货地址')
                self.fields['video']=serializers.SerializerMethodField(label='商品信息')
        if self.context['view'].basename == 'cms-order':
            self.fields['user']=serializers.CharField(label='用户名称')

    def get_video(self,obj):
        return obj.order_set.all().values()

    def get_alipay_url(self, obj):
        """拿到支付宝给的url 传递给前端  让前端再去跳转至支付宝url"""
        alipay = AliPay(
            appid="2016092500593195",
            app_notify_url="http://127.0.0.1:8000/alipay/return/",
            app_private_key_path=PRIVATE_KEY,
            alipay_public_key_path=PUL_KEY,  # 此处发请求为自己的公钥
            debug=True,  # 默认False,
            return_url="http://127.0.0.1:8000/alipay/return/"
        )
        url = alipay.direct_pay(
            subject=str(obj.order_sn),
            out_trade_no=str(obj.order_sn),
            total_amount=float(obj.order_mount),  # obj.order_mount,
            return_url="http://127.0.0.1:8000/alipay/return/"
        )
        re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
        return re_url

    def validate_video_ids(self,attr):
        attr=re.split(r',',attr)
        return [i for i in attr if i.isnumeric()]

    def validate(self, attrs):
        video_ids=attrs.pop('video_ids')
        res = self.redis.hgetall(self.shopping_key(attrs['user'].id))
        self.order=[]
        try:
            for i in video_ids:
                user_count=int(res.get(i))
                temp=Order()
                # 悲观锁
                temp.video=VideoSKU.objects.select_for_update().get(id=i)
                if temp.video.stock<user_count:
                    raise ValidationError({'error':'商品库存不足'})
                temp.video.stock-=user_count
                temp.video.save()

                temp.video_num=user_count
                temp.price=temp.video.price
                self.order.append(temp)
        except ObjectDoesNotExist :
            raise ValidationError({'error':'商品不存在'})
        # import time
        # time.sleep(10)
        # print(f'当前是{attrs["post_script"]}',datetime.datetime.now())
        attrs['order_mount']= sum([dict.price*dict.video_num for dict in self.order ])
        attrs['order_sn']=uuid.uuid3(uuid.NAMESPACE_DNS,f"{attrs['user'].id}{uuid.uuid1()}")
        return attrs

    @staticmethod
    def shopping_key(id):
        return f'shopping_{id}'

    def create(self, validated_data):
        instance=self.Meta.model.objects.create(**validated_data)
        for i in self.order:
            i.order=instance
        Order.objects.bulk_create(self.order)
        #self.redis.hdel(self.shopping_key(instance.user_id),*[i.video_id for i in self.order])
        return instance

    class Meta:
        model=OrderInfo
        exclude=('is_active','order_mount','pay_time')