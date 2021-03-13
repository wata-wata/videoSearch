from django.urls import path
from .views import *

urlpatterns = [
  path("test", testfunc, name="test"),
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
  # マイリスト(カテゴリ一覧)
  path("mylist/", mylistfunc, name="mylist"),
  # マイリスト(カテゴリ別)
  path("mylist_category/<str:pk>", mylist_categoryfunc, name="mylist_category"),
  # マイリスト(動画追加)
  path("mylist_add", addMylistFunc, name="mylist_add"),
]
