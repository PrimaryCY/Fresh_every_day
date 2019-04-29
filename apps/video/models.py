import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey

from utils.models import BaseModel
from apps.user.models import User,Department,UserAddress



class Banner(BaseModel):

    BANNER_TYPE=(
        (1,'视频'),
        (2,'视频集')
    )
    index=models.SmallIntegerField(default=0,verbose_name='轮播顺序')
    img=models.ImageField(verbose_name='轮播图片',null=True,blank=True)
    create_user=models.ForeignKey(User,on_delete=models.CASCADE,verbose_name='创建人')
    #type=models.SmallIntegerField(choices=BANNER_TYPE,verbose_name='资源类型')
    table_name=models.ForeignKey(ContentType,on_delete=models.CASCADE,null=True,blank=True,
                                 verbose_name='关联表名称')
    table_id=models.PositiveIntegerField(verbose_name='关联表的id',null=True,blank=True)
    content_obj=GenericForeignKey('table_name','table_id')
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,verbose_name='所属部门',null=True,blank=True)

    def __str__(self):
        return self.table_name

    class Meta:
        verbose_name_plural=verbose_name='轮播图表'

    @classmethod
    def get_web_banners(cls,dept_ids,limit,context):
        queryset=cls.objects.filter(department__in=dept_ids).order_by('-created_time')[:limit]
        from apps.video.serializer import BannerSerializer
        return BannerSerializer(queryset,many=True,context=context).data


class VideoCategory(MPTTModel):
    parent = TreeForeignKey('self', on_delete=models.CASCADE, related_name='child',
                            verbose_name='父类', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='类别名称')
    desc = models.TextField(max_length=100, verbose_name='类别描述')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    image=models.ImageField(null=True,blank=True,verbose_name='Icon')

    class Meta:
        verbose_name_plural=verbose_name='视频种类表'

    def __str__(self):
        return self.name

    @classmethod
    def get_promotionvideo(cls, dept_ids, limit, context):
        queryset = cls.get_queryset()[:limit]
        from apps.video.serializer import ListShowVideoSerializer
        return ListShowVideoSerializer(queryset, many=True, context=context).data

    @classmethod
    def get_queryset(cls):
        now = datetime.datetime.now()
        return cls.objects.filter(stop_date__gte=now).order_by('-created_time')


class VideoSPU(BaseModel):

    name=models.CharField(max_length=50,verbose_name='商品名称')
    message=models.CharField(max_length=100,null=True,blank=True,verbose_name='商品留言')
    category=models.ForeignKey(VideoCategory,null=True,blank=True,on_delete=models.SET_NULL,verbose_name='商品类别')
    comment=models.DecimalField(default=3.5,max_digits=5,decimal_places=1,verbose_name='视频评分')
    after_service=models.TextField(verbose_name='商品售后服务')
    desc=models.TextField(verbose_name='商品简介',null=True,blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='所属部门', null=True, blank=True)

    class Meta:
        verbose_name_plural=verbose_name='视频SPU表'

    def __str__(self):
        return self.name


class VideoSKU(BaseModel):

    VIDEO_SPCIFICATION=(
        (0,'标清'),
        (1,'高清'),
        (2,'超清')
    )
    spu=models.ForeignKey(VideoSPU,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='视频关联SPU表')
    specification=models.SmallIntegerField(choices=VIDEO_SPCIFICATION,verbose_name='视频规格')
    stock=models.IntegerField(default=0,verbose_name='库存')
    image=models.ImageField(verbose_name='视频封面图片',blank=True,null=True)
    price=models.FloatField(default=0,verbose_name='视频价格')
    file=models.FileField(verbose_name='视频文件')

    def __str__(self):
        return f"{self.spu.name}{self.specification}"

    class Meta:
        verbose_name_plural=verbose_name='视频SKU表'
        unique_together =(("spu","specification"),)


class PromotionVideo(BaseModel):
    spu=models.ForeignKey(VideoSPU,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='促销视频')
    image=models.ImageField(verbose_name='促销封面',null=True,blank=True)
    index=models.SmallIntegerField(default=0,verbose_name='促销展示顺序')
    stop_date=models.DateField(verbose_name='促销结束时间')
    title=models.CharField(max_length=50,verbose_name='首页促销标题')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='所属部门', null=True, blank=True)

    class Meta:
        verbose_name_plural=verbose_name='首页促销视频表'

    def __str__(self):
        return self.title

    @classmethod
    def celery_destory_instance(cls,request):
        now = datetime.datetime.now()
        cls.objects.filter(department__in=request.dept_ids, stop_date__gte=now).order_by('index')

    @classmethod
    def get_promotionvideo(cls, dept_ids, limit, context):
        queryset = cls.get_queryset(dept_ids)[:limit]
        from apps.video.serializer import CMSPromotionVideoSerializer
        return CMSPromotionVideoSerializer(queryset, many=True, context=context).data

    @classmethod
    def get_queryset(cls,dept_ids):
        now = datetime.datetime.now()
        return cls.objects.filter(department__in=dept_ids,stop_date__gte=now).order_by('-created_time')


class ShowVideo(BaseModel):
    SHOW_WAY=(
        (0,'图片'),
        (1,'文字')
    )
    index=models.SmallIntegerField(default=0,verbose_name='展示顺序')
    spu=models.ForeignKey(VideoSPU,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='视频spu表')
    category=models.ForeignKey(VideoCategory,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='视频分类表')
    stop_time=models.DateField(verbose_name='展示停止时间')
    show_way=models.SmallIntegerField(choices=SHOW_WAY,verbose_name='展示方式')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='所属部门', null=True, blank=True)

    class Meta:
        verbose_name_plural=verbose_name='首页展示表'

    def __str__(self):
        return self.spu.name

    @classmethod
    def get_showvideo(cls, limit, context):
        queryset=cls.get_queryset()[:limit]
        from apps.video.serializer import ListShowVideoSerializer
        data=ListShowVideoSerializer(queryset, many=True, context=context).data
        return [dict for dict in data if dict['spu'].exists()]

    @classmethod
    def get_queryset(cls):
        return VideoCategory.objects.filter(level=0).order_by('-created_time')


class OrderInfo(BaseModel):
    # 支付宝返回的五种支付状态
    ORDER_STATUS = (
        ("TRADE_SUCCESS", "成功"),
        ("TRADE_CLOSED", "超时关闭"),
        ("WAIT_BUYER_PAY", "交易创建"),
        ("TRADE_FINISHED", "交易结束"),
        ("PAYING", "待支付"),
        ("USER_CANCELLED",'用户取消'),
        ("BACKGROUND_CANCEL",'后台取消')
    )

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name='用户')
    order_sn = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name='订单编号')
    trade_no = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='交易编号')
    pay_status = models.CharField(max_length=30, verbose_name='订单状态', choices=ORDER_STATUS, default='paying')
    post_script = models.TextField(verbose_name='订单留言')
    order_mount = models.FloatField(default=0.0, verbose_name='订单金额')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    address = models.ForeignKey(UserAddress,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='收件地址')

    def __str__(self):
        return self.order_sn

    class Meta:
        verbose_name =verbose_name_plural= '订单信息'


class Order(BaseModel):
    video=models.ForeignKey(VideoSKU,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='视频')
    order=models.ForeignKey(OrderInfo,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='订单详细信息')
    video_num=models.IntegerField(verbose_name='视频数量')

    class Meta:
        verbose_name=verbose_name_plural='订单视频'

    def __str__(self):
        return f"{self.video}{self.order}{self.video_num}"