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

# youtube --------------------------------------------------------------------------
@login_required
def youtube_searchfunc(request):
  params = {'word': '', 'form': None, 'result': []}
  if request.method == 'POST': # フォームが送信されたとき
    # print(request.POST)
    # print(request.POST.getlist('video', False))
    is_exist_word = request.POST.get('word', False)
    if is_exist_word != False: # 検索キーワードを受け取って検索する
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
          # q="ポケモン", # 検索キーワード
          q=word, # 検索キーワード
          part="id,snippet",
          maxResults=25,
        ).execute()

      videos = []
      channels = []
      playlists = []

      i = 0
      for search_result in search_response.get("items", []):
          # if i == 0:
          #   print(i)
            # print(search_result)
            # print(search_result["snippet"]["publishedAt"]) # 投稿日時
            # print(search_result["snippet"]["description"]) # 概要欄の文章
            # print(search_result["snippet"]["thumbnails"]["default"]["url"]) # サムネイルの画像のURL
            
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

            params['result'].append(d)

          elif search_result["id"]["kind"] == "youtube#channel":
            channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                        search_result["id"]["channelId"]))
          elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                          search_result["id"]["playlistId"]))

    else:
      # (マイリストに追加する処理)
      is_exist_video = request.POST.getlist('video', False)
      if is_exist_video != False: # 1つ以上選択されたとき
        # 選択した動画をマイリストに追加する
        for v in is_exist_video:
          r = ast.literal_eval(v) # 文字列から辞書に変換する
          print(r)
          print(type(r))
          print(r['title'])
          
          qd = QueryDict(
            'title='+r["title"]+
            '&url='+r["url"]+
            '&thumbnail='+r["thumbnail"]
          )
          print(qd)

          form = MyVideo(user=request.user, data=qd)
          print(type(request.user))
          # insert処理(Videoモデルに追加する)
          if form.is_valid():
            create_myvideo = Video(
              title=qd['title'],
              url=qd['url'],
              thumbnail=qd['thumbnail'],
              user=request.user
            )
            create_myvideo.save()
            messages.success(request, r["title"]+'をマイリストに保存しました')
          else:
            messages.error(request, r["title"]+"は既に保存されています")

      else:
        messages.error(request, "動画を1つ以上選択してください")

    params['form'] = SearchForm()

  else: # 最初に関数が呼ばれたとき
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

    else:
      # マイリストに追加する処理
      is_exist_video = request.POST.getlist('video', False)
      if is_exist_video != False: # 1つ以上選択されたとき
        # 選択した動画をマイリストに追加する
        for v in is_exist_video:
          r = ast.literal_eval(v) # 文字列から辞書に変換する
          print(r)
          print(type(r))
          print(r['title'])

          qd = QueryDict(
            'title='+r["title"]+
            '&url='+r["url"]+
            '&thumbnail='+r["thumbnail"]
          )
          print(qd)

          form = MyVideo(user=request.user, data=qd)
          print(type(request.user))
          # insert処理(Videoモデルに追加する)
          if form.is_valid():
            create_myvideo = Video(
              title=qd['title'],
              url=qd['url'],
              thumbnail=qd['thumbnail'],
              user=request.user
            )
            create_myvideo.save()
            messages.success(request, r["title"]+'をマイリストに保存しました')
          else:
            messages.error(request, r["title"]+"は既に保存されています")
      else:
        messages.error(request, "動画を1つ以上選択してください")

    params['form'] = SearchForm()
  
  else: # 最初に関数が呼ばれたとき
    params['form'] = SearchForm()
  return render(request, 'niconico_search.html', params)

# マイリスト
class mylistView(View, LoginRequiredMixin):
  def get(self, request, *args, **kwargs): # 最初に読み込まれたとき
    context = {
      "mylist": Video.objects.filter(user=request.user).order_by("-id")
    }
    return render(request, "mylist.html", context)

# マイリスト削除
class deleteMylistView(View, LoginRequiredMixin):
  def post(self, request, *args, **kwargs):
    '''searchRusult.html post処理'''
    videos = self.request.POST.getlist('video',[])
    print(videos)
		# 1つ以上選択された時
    if videos != []:
      for video in videos:
        selected_title = Video.objects.get(title=video).title
        print(selected_title)
        Video.objects.filter(title=video).delete() # モデルから削除する
        messages.success(request, selected_title+'をマイリストから削除しました')

      context = {
      # select処理
			'mylist': Video.objects.filter(user=self.request.user).order_by('-id')
			}
      return render(request, 'mylist.html', context)
      return HttpResponse(status=204)

		# 1つも選択されなかった時
    else:
      messages.error(request,"最低1つ以上選択してください")
      return redirect('mylist')

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

        return redirect("site_user_profile")

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