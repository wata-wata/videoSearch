from videoapp.models import *
from django.shortcuts import redirect, render
from django.http import HttpResponse, QueryDict
import requests
import json
from .forms import *
from django.views import View
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
import ast
from .constant import * # constant.pyからkeyを読み込む

# youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
# DEVELOPER_KEY = DEVELOPER_KEY
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def testfunc(request):
  return render(request, 'youtube_search.html')

# youtube --------------------------------------------------------------------------
@login_required
def youtube_searchfunc(request):
  params = {'word': '', 'form': None, 'result': []}
  if request.method == 'POST': # フォームが送信されたとき
    # print(request.POST)
    # print(request.POST.getlist('video', False))
    is_exist_word = request.POST.get('word', False)
    if is_exist_word != False: # 「検索」ボタンが押されたとき
      # 検索キーワードを受け取って検索する
      # print(request.POST['word'])
      # keyに対応するvalueがあるかどうかでformのPOST処理を分ける
      form = SearchForm(request.POST)
      params['word'] = request.POST['word']
      params['form'] = form
      word = request.POST['word'] # 検索キーワード

      # 検索する
      youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
          developerKey=DEVELOPER_KEY)

      search_response = youtube.search().list(
          q=word, # 検索キーワード
          part="id,snippet",
          maxResults=25,
        ).execute()

      videos = []
      channels = []
      playlists = []

      i = 0
      for search_result in search_response.get("items", []):
          if i < 2: # テスト
            print(search_result)
            # print(search_result["snippet"]["channelTitle"]) # チャンネル名
            # print(search_result["id"]["videoId"]) # id
            # idから再生回数を取得する
            # id = search_result["id"]["videoId"]
            # statistics = youtube.videos().list(part = 'statistics', id = id).execute()['items'][0]['statistics']
            # print(statistics)
          i += 1
          if search_result["id"]["kind"] == "youtube#video":
            videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                      search_result["id"]["videoId"]))
            # 辞書型
            d = {}
            # 動画のタイトル
            d['title'] = search_result["snippet"]["title"]
            # params['result'].append(search_result["snippet"]["title"])
            # 動画のURL
            d['url'] = "https://www.youtube.com/watch?v=" + search_result["id"]["videoId"]
            # params['result'].append("https://www.youtube.com/watch?v=" + search_result["id"]["videoId"])
            # サムネイルの画像のURL
            d['thumbnail'] = search_result["snippet"]["thumbnails"]["default"]["url"]
            # チャンネル名
            d['channelTitle'] = search_result["snippet"]["channelTitle"]
            # idから再生回数を取得する
            id = search_result["id"]["videoId"]
            viewCount = youtube.videos().list(part = 'statistics', id = id).execute()['items'][0]['statistics']
            d['viewCount'] = viewCount["viewCount"]

            params['result'].append(d)

          elif search_result["id"]["kind"] == "youtube#channel":
            channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                        search_result["id"]["channelId"]))
          elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                          search_result["id"]["playlistId"]))

    # 「マイリストに追加」ボタンが押されたとき、mylist_add.htmlに遷移する
    elif request.POST.get('title', False) != False:
      # print(request.POST.get('title', False))
      d = {}
      d['title'] = request.POST['title']
      d['url'] = request.POST['url']
      d['thumbnail'] = request.POST['thumbnail']
      # d['categories'] = VideoCategory.objects.all # カテゴリ一覧
      d['categories'] = VideoCategory.objects.filter(user=request.user).distinct()
      return render(request, 'mylist_add.html', d)

    params['form'] = SearchForm()

  else: # request.method == 'GET'(最初に関数が呼ばれたとき)
    params['form'] = SearchForm()

  return render(request, 'youtube_search.html', params)

# niconico --------------------------------------------------------------------------
@login_required
def niconico_searchfunc(request):
  params = {'word': '', 'form': None, 'result': []}
  if request.method == 'POST': # フォームが送信されたとき
    is_exist_word = request.POST.get('word', False)
    if is_exist_word != False: # 検索キーワードを受け取って検索する
      form = SearchForm(request.POST)
      params['word'] = request.POST['word']
      params['form'] = form
      word = request.POST['word'] # 検索キーワード

      # 検索する
      REQUEST_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

      # JSONフィルタ指定仕様
      jsonFilter = """{
        "type": "or",
        "filters": [
          {
            "type": "range",
            "field": "startTime",
            "from": "2017-07-07T00:00:00+09:00",
            "to": "2017-07-08T00:00:00+09:00",
            "include_upper": false
          },
          {
            "type": "range",
            "field": "startTime",
            "from": "2016-07-07T00:00:00+09:00",
            "to": "2016-07-08T00:00:00+09:00",
            "include_upper": false
          }
        ]
      }"""

      # クエリ文字列仕様
      query = {
          'q':word,
          'targets':'title,tags',
          'fields':'contentId,title,viewCounter,thumbnailUrl',
          '_sort':'viewCounter',
          '_context':'nico_jsonFilter',
          '_limit':10,
          # 'jsonFilter':jsonFilter # 条件を絞る
      }

      # データを取得する
      responses = requests.get(REQUEST_URL, query).json()

      for i in range(len(responses['data'])):
        d = {} # 辞書型
        d['title'] = responses['data'][i]['title']
        d['viewCounter'] = responses['data'][i]['viewCounter']
        d['thumbnail'] = responses['data'][i]['thumbnailUrl']
        d['url'] = "https://nico.ms/" + responses['data'][i]['contentId']
        params['result'].append(d)

    # 「マイリストに追加」ボタンが押されたとき、mylist_add.htmlに遷移する
    elif request.POST.get('title', False) != False:
      print(request.POST.get('title', False))
      d = {}
      d['title'] = request.POST['title']
      d['url'] = request.POST['url']
      d['thumbnail'] = request.POST['thumbnail']
      # d['categories'] = VideoCategory.objects.all # カテゴリ一覧
      d['categories'] = VideoCategory.objects.filter(user=request.user).distinct()
      return render(request, 'mylist_add.html', d)

    params['form'] = SearchForm()
  
  else: # 最初に関数が呼ばれたとき
    params['form'] = SearchForm()
  return render(request, 'niconico_search.html', params)

# マイリスト(カテゴリ一覧)
class mylistView(View, LoginRequiredMixin):
  def get(self, request, *args, **kwargs): # 最初に読み込まれたとき
    # カテゴリを全て取得する(名前でソートする)
    categories = []
    for i in VideoCategory.objects.filter(user=request.user).order_by("name").distinct().values("name"):
      print(i["name"])
      print(type(i["name"]))
      categories.append(i["name"])
    print(categories)
    context = {
      "mylist": Video.objects.filter(user=request.user).order_by("-id"),
      # カテゴリをVideoモデルから、user名指定→カテゴリ重複しないように取ってきたい
      "categories": categories
    }
    return render(request, "mylist.html", context)

  def post(self, request, *args, **kwargs):
    print(request.POST)
    if request.POST.get("category_add", False) != False:
      # カテゴリを追加する
      category_add = request.POST["category_add"] # 追加するカテゴリ
        
      form = VideoCategoryReservationForm({
        "name":category_add,
        "user":request.user
      })

      if form.is_valid() == True:
        # モデル「VideoCategory」に追加する
        vc = VideoCategory(
          name=category_add,
          user=request.user
        )
        vc.save() # VideoCategoryモデルに追加する
        messages.success(request,"カテゴリ「" + category_add + "」が追加されました")
      else: # 同じデータが既にあるとき
        messages.error(request, "カテゴリ「" + category_add + "」は既に存在します")
    else:
      # カテゴリが入力されなかったとき
      messages.error(request,"追加するカテゴリを入力してください")

    # カテゴリを全て取得する
    categories = []
    for i in VideoCategory.objects.filter(user=request.user).order_by("name").distinct().values("name"):
      print(i["name"])
      print(type(i["name"]))
      categories.append(i["name"])
    print(categories)
    context = {
      "mylist": Video.objects.filter(user=request.user).order_by("-id"),
      # カテゴリをVideoモデルから、user名指定→カテゴリ重複しないように取ってきたい
      "categories": categories
    }

    return render(request, "mylist.html", context)

# マイリスト(カテゴリ別)
@login_required
def mylist_categoryfunc(request, pk):
  # pk: 選択したカテゴリの名前
  print(pk)
  print(type(pk))

  if request.method == "POST": # 削除する動画を選択したとき
    # 選択した動画を削除する
    category_name = request.POST.get("category_name")
    print(category_name)
    print(type(category_name))

    video_list = request.POST.getlist("check_delete")
    print(video_list) # 選択しなかったら[]になる

    # 動画が1つ以上選択されたとき
    if video_list != []:
      for i in video_list:
        print(i)
        # string → dict
        i = ast.literal_eval(i)
        print(i["title"])

        # Videoモデルから削除する
        v = Video.objects.filter(user=request.user).filter(category__name=category_name).filter(title=i["title"])
        v.delete()
        messages.success(request, i["title"] + "をカテゴリ「" + category_name + "」から削除しました")

    # 1つも選択されなかったとき
    else:
      messages.error(request,"動画を1つ以上選択してください")

  # 選択したカテゴリの動画のタイトルを取得する
  # category__name: VideoCategoryモデルのname
  video = Video.objects.filter(user=request.user).filter(category__name=pk)

  print(video)

  # titles = []
  video_info = []
  for i in video:
    d = {}
    # タイトル
    title = str(i)
    # titles.append(title)
    d["title"] = title
    
    v = Video.objects.filter(user=request.user).filter(category__name=pk).filter(title=title)
    # URL
    print(v[0].url)
    d["url"] = v[0].url
    # サムネイル
    print(v[0].thumbnail)
    d["thumbnail"] = v[0].thumbnail

    video_info.append(d)

  if video_info == []:
    messages.error(request, "このカテゴリには動画が追加されていません")

  params = {
    "pk":pk,
    "video_info":video_info
  }

  return render(request, "mylist_category.html", params)

# マイリスト追加
@login_required
def addMylistFunc(request):
  # print("called addMylistFunc")
  if request.method == 'POST':
    # 動画を、選択されたカテゴリのマイリストに追加する
    # print(request.POST)

    # print(request.POST['title']) # 動画のタイトル
    # print(request.POST['url']) # 動画のURL
    # print(request.POST['thumbnail']) # 動画のサムネイル
    # print(request.user) # ログインしているユーザー

    d = {}
    d["title"] = request.POST["title"]
    d["url"] = request.POST["url"]
    d["thumbnail"] = request.POST["thumbnail"]
    d["categories"] = VideoCategory.objects.filter(user=request.user).distinct()

    category_checked = False # カテゴリが1つ以上選択されていればTrue

    for key in request.POST:
      if(request.POST[key]=='on'):
        category_checked = True

        print(request.POST['url'])
        print(VideoCategory.objects.filter(name=key)[0].name)

        # 重複しているデータがあるか判定する
        form = VideoReservationForm({
          'url':request.POST['url'],
          'user':request.user,
          'category':VideoCategory.objects.filter(name=key)[0]
        })

        print(form.is_valid()) # Trueならモデルに追加する

        if form.is_valid() == True:
          # モデル「Video」に追加する ---------------
          v = Video(
            title=request.POST['title'],
            url=request.POST['url'],
            thumbnail=request.POST['thumbnail'],
            user=request.user,
            category=VideoCategory.objects.filter(name=key)[0]
          )
          v.save() # 「Video」モデルに追加する
          messages.success(request, request.POST['title'] + "をマイリスト(" + key + ")に追加しました")
        else: # 同じデータが既にあるとき
          messages.error(request, request.POST['title'] + "は既にマイリスト(" + key + ")に保存されています")

    if category_checked == False: # カテゴリが1つも選択されていないとき
      messages.error(request,"最低1つ以上選択してください")

  return render(request, "mylist_add.html", d)

# ログイン
class SiteUserLoginView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "form": SiteUserLoginForm(),
        }
        return render(request, "siteUser/login.html", context)

    def post(self, request, *args, **kwargs):
        form = SiteUserLoginForm(request.POST)
        if not form.is_valid():
            return render(request, "siteUser/login.html", {"form": form})

        login_site_user = form.get_site_user()

        auth_login(request, login_site_user)

        messages.success(request, "ログインしました")

        # ログインしたらyoutube検索に遷移する
        return redirect("../youtube_search")

# ログアウト
class SiteUserLogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            auth_logout(request)

        messages.success(request, "ログアウトしました")

        return redirect("site_user_login")
        
# 会員登録
class SiteUserRegisterView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "form": SiteUserRegisterForm(),
        }
        return render(request, "siteUser/register.html", context)

    def post(self, request, *args, **kwargs):
        form = SiteUserRegisterForm(request.POST)
        if not form.is_valid():
            return render(request, "siteUser/register.html", {"form": form})

        new_site_user = form.save(commit=False)
        new_site_user.set_password(form.cleaned_data["password"])

        new_site_user.save()
        messages.success(request, "会員登録が完了しました")
        return redirect("site_user_login")


class SiteUserProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        return render(request, "siteUser/profile.html")