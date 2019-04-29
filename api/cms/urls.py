# -*- coding: utf-8 -*-
# author:CY
# datetime:2019/3/30 21:44
from django.conf.urls import url,include

from api.cms.user import LoginViewSet,SmsViewSet,UserViewSet,AllUserAddrViewSet,\
    DepartmentViewSet,TreeViewSet,MeanViewSet,RoleViewSet,UserRoleViewSet,CmsRoleViewSet
from api.web.user import EmailViewSet,PersonalUserViewSet,UserAddrViewSet
from api.cms.video import BannerViewSet,CMSVideoCategoryViewSet,CMSVideoSpuViewSet,\
    CMSVideoSkuViewSet,CMSPromotionVideoViewSet,CMSShowVideoViewSet
from api.web.video import WebBannerViewSet,WebVideoCategory,WebVideoSPUViewSet,\
    IndexViewSet,BrowsingHistoryViewSet,ShoppingCartViewSet,OrderViewSet,CMSOrderViewSet
from utils.routes import CustomRouter

router=CustomRouter()
router.register('cms/user',UserViewSet,base_name='user')        #后台权限部门下所有用户信息
router.register('cms/address',AllUserAddrViewSet,base_name='all_user_address')#后台该部门下的用户地址
router.register('cms/department',DepartmentViewSet,base_name='department')#后台部门
router.register('cms/mean',MeanViewSet,base_name='mean')                    #后台菜单
router.register('cms/roles',RoleViewSet,base_name='role')                   #角色管理
router.register('cms/user-role',CmsRoleViewSet,base_name='user-role')        #用户角色管理
router.register('cms/banner',BannerViewSet,base_name='banner')              #轮播图管理
router.register('cms/video-category',CMSVideoCategoryViewSet,base_name='cms-video-category')   #视频分类管理
router.register('cms/videospu',CMSVideoSpuViewSet,base_name='cms-video-spu')        #视频spu设置
router.register('cms/videosku',CMSVideoSkuViewSet,base_name='cms-video-sku')        #视频sku设置
router.register('cms/promotion-video',CMSPromotionVideoViewSet,base_name='cms-promotion-video')   #促销视频
router.register('cms/showvideo',CMSShowVideoViewSet,base_name='cms-showvideo')      #后台设置分类置顶视频
router.register('cms/cms-order',CMSOrderViewSet,base_name='cms-order')
router.register('test/tree',TreeViewSet,base_name='tree')
router.register('web/order',OrderViewSet,base_name='order')                         #提交订单,查看个人订单
router.register('web/shopping-cart',ShoppingCartViewSet,base_name='shopping-cart')  #购物车显示
router.register('web/browsing-history',BrowsingHistoryViewSet,base_name='history')  #用户浏览记录
router.register('web/index',IndexViewSet,base_name='index')                         #web首页
router.register('web/video-spu',WebVideoSPUViewSet,base_name='web-video-spu')       #web展示spu视频信息
router.register('web/video-category',WebVideoCategory,base_name='web-video-category')   #web展示视频分类
router.register('web/user-role',UserRoleViewSet,base_name='switch-role')      #切换角色
router.register('web/login',LoginViewSet,base_name='login')                 #用户登录
router.register('web/sms',SmsViewSet,base_name='sms')                       #用户短信登录
router.register('web/email',EmailViewSet,base_name='email')                 #用户修改密码
router.register('web/PersonalUser',PersonalUserViewSet,base_name='personaluser')#用户个人信息
router.register('web/address',UserAddrViewSet,base_name='user_address')     #用户个人地址
router.register('web/banner',WebBannerViewSet,base_name='web-banner')       #轮播图



urlpatterns = [

    url(r'^',include(router.urls))
]
