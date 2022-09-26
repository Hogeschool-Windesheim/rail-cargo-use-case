from django.urls import path, re_path
from django.views.generic import TemplateView

from rest_framework.schemas import get_schema_view

from .views import views
from .views import UserViews
from .views import SettingViews
from .views import SlpIdViews
from .views import AddressbookViews
from .views import PublicationViews
from .views import TokenViews
from .views import AssetViews, OrderViews, EventViews

from .standards import RegexPatterns as Pattern

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^auth_token/?$', TokenViews.CreateTokenViews.as_view(), name='create_token'),
    re_path(r'^auth_token/(?P<username>[0-9a-zA-Z]+)/(?P<password>[a-z0-9A-Z_\-:]+)/?$', TokenViews.TokenViews.as_view(), name='get_token'),
    path('openapi/', get_schema_view(
            title="Full Truck Load API",
            description="FTL API documentation page",
            version="1.0.0",
        ), name='openapi-schema'),
    path('docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),

    re_path(r'^setting/?$', SettingViews.SettingList.as_view(), name='settings'),
    re_path(r'^setting/(?P<setting>{0})/?$'.format(Pattern.setting),
        SettingViews.SettingDetail.as_view(), name='setting'),

    re_path(r'^user/?$', UserViews.UserListView.as_view(), name='user_view'),
    re_path(r'^user/(?P<username>{})/?$'.format(Pattern.username),
        UserViews.UserDetailView.as_view(), name='user_view'),

    re_path(r'^raw_publication/?$',
        PublicationViews.RawPublicationsView.as_view(), name='raw_publication'),
    
    re_path(r'^slp_id/?$', SlpIdViews.SlpIdList.as_view(), name='slp_list'),
    re_path(r'^slp_id/(?P<alias>{})/?$'.format(Pattern.slpID),
        SlpIdViews.SlpIdDetail.as_view(), name='slp_detail'),
    re_path(r'^address/?$', AddressbookViews.AddressbookList.as_view(), name='address_list'),
    re_path(r'^address/(?P<alias>{})/?$'.format(Pattern.slpID),
        AddressbookViews.AddressbookDetail.as_view(), name='address_detail'),
    re_path(r'^assets/?$', AssetViews.MyAssets.as_view(), name='my_assets'),

    re_path(r'^transfer/?$', AssetViews.TransferAsset.as_view(), name="transfer"),

    # Project-specific URLs start here
    re_path(r'^orders/?$', OrderViews.OrderView.as_view(), name="order"),
    re_path(r'^orders/(?P<asset_id>{})/?$'.format(Pattern.assetID),
        OrderViews.OrderDetailView.as_view(), name="order_detail"),
    re_path(r'^events/?$', EventViews.EventView.as_view(), name="event")
]
