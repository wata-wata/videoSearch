from django.urls import path
from .views import *

urlpatterns = [
  # ログイン認証
  path("siteUser/login", SiteUserLoginView.as_view(), name="site_user_login"),
  path("siteUser/logout", SiteUserLogoutView.as_view(), name="site_user_logout"),
  path("siteUser/register", SiteUserRegisterView.as_view(), name="site_user_register"),
  path("siteUser/profile", SiteUserProfileView.as_view(), name="site_user_profile"),
  # ニコニコ
  path("niconico_search/", niconico_searchfunc, name='niconico_search'),
  # youtube検索
  path("youtube_search/", youtube_searchfunc, name='youtube_search'),
  path("", youtube_searchfunc, name='youtube_search'),
  # マイリスト
  path("mylist/", mylistView.as_view(), name="mylist"),
  # マイリスト削除
  path("mylist_delete/", deleteMylistView.as_view(), name="mylist_delete"),
]
