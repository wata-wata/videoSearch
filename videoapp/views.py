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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
from os.path import join, dirname
from dotenv import load_dotenv

# youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# トップページ
def topfunc(request):
  return render(request, "top.html")

# youtube --------------------------------------------------------------------------
def youtube_searchfunc(request):
  def searchfunc(word, sort): # 検索する関数
    # APIキーの取得
    # load_dotenv('.env') # localのみ

    DEVELOPER_KEY = os.environ.get("youtube_key") # 本番環境

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
          developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=word, # 検索キーワード
        part="id,snippet",
        maxResults=50, # 取得する動画の数
        order=sort # order: 並び替える基準
      ).execute()

    videos = []
    channels = []
    playlists = []

    # データベースに保存されている検索結果を削除する -----------
    SearchResult.objects.all().delete()

    i = 0
    for search_result in search_response.get("items", []):
        i += 1
        if search_result["id"]["kind"] == "youtube#video":
          videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                    search_result["id"]["videoId"]))
          # 辞書型
          d = {}
          # 動画のタイトル
          d["title"] = search_result["snippet"]["title"]
          # 動画のURL
          d["url"] = "https://www.youtube.com/watch?v=" + search_result["id"]["videoId"]
          # サムネイルの画像のURL
          d["thumbnail"] = search_result["snippet"]["thumbnails"]["default"]["url"]
          # チャンネル名
          d["channelTitle"] = search_result["snippet"]["channelTitle"]
          # idから再生回数を取得する
          id = search_result["id"]["videoId"]
          viewCount = youtube.videos().list(part = "statistics", id = id).execute()["items"][0]["statistics"]
          d["viewCount"] = viewCount["viewCount"]

          params["result"].append(d) # 検索結果を保存する -----------

          # 検索結果をデータベースに保存する -----------
          r = SearchResult(
            title=search_result["snippet"]["title"],
            url="https://www.youtube.com/watch?v=" + search_result["id"]["videoId"],
            thumbnail=search_result["snippet"]["thumbnails"]["default"]["url"],
            viewCount=viewCount["viewCount"]
          )
          r.save() # SearchResultモデルに追加する

        elif search_result["id"]["kind"] == "youtube#channel":
          channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                      search_result["id"]["channelId"]))
        elif search_result["id"]["kind"] == "youtube#playlist":
          playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                        search_result["id"]["playlistId"]))

  params = { # 渡すデータ
    "word": "",
    "form": None,
    "result": [],
    "sort": "関連性が高い順"
  }

  if request.method == "POST": # フォームが送信されたとき
    # 並び替えのボタン(関連性が高い順など)が押されたとき
    if request.POST.get("sort", False) != False:
      if request.GET.get('word', False) == False: # 検索ワードが入っていないとき
        # エラー処理
        messages.error(request, "キーワードを入力してください")

      # else: # 検索ワードが入っているとき
      if request.GET.get("word", False) != False: # 検索されたとき
        if request.GET["word"] == "": # 検索ワードが入っていないとき
          # エラー処理
          messages.error(request, "キーワードを入力してください")
        else:
          sort = request.POST["sort"]
          word = request.GET["word"]
          params["sort"] = sort # テキストを変更する

          # 指定された条件で検索する -------------------
          if sort == "関連性が高い順":
            searchfunc(word, "relevance") # 検索する
          elif sort == "投稿日時が新しい順":
            searchfunc(word, "date") # 検索する
          elif sort == "評価の高い順":
            searchfunc(word, "rating") # 検索する
          elif sort == "再生回数の多い順":
            searchfunc(word, "viewCount") # 検索する

          # ページング処理 -----------
          page = 1 # 1ページ目を表示するようにする --------

          # 1ページに表示するデータ数を指定する
          paginator = Paginator(params["result"], 10)
          try:
            results = paginator.page(page)
          except PageNotAnInteger:
            results = paginator.page(1)
          except EmptyPage:
            results = paginator.page(paginator.num_pages)
          params["result"] = results

    # 「マイリストに追加」ボタンが押されたとき、mylist_add.htmlに遷移する
    elif request.POST.get("title", False) != False:
      if not request.user.is_authenticated: # ログイン認証
        messages.error(request, "ログインしてください")
        return redirect("/siteUser/login")
      d = {}
      d["title"] = request.POST["title"]
      d["url"] = request.POST["url"]
      d["thumbnail"] = request.POST["thumbnail"]
      d["categories"] = VideoCategory.objects.filter(user=request.user).order_by("name").distinct()

      return render(request, "mylist_add.html", d)

    params["form"] = SearchForm()

  elif request.method == "GET":
    params["form"] = SearchForm()

    is_exist_word = request.GET.get("word", False)
    if is_exist_word != False: # 「検索」ボタンが押されたとき、ページ番号が異なるページから遷移したとき
      if request.GET["word"] == "": # 検索ワードが入っていないとき
        # エラー処理
        messages.error(request, "キーワードを入力してください")

      else:
        # ページ遷移の場合は、params["sort"]を更新する
        # 「検索」ボタンが押された場合は、関連性が高い順に検索する
        if request.GET.get("sort", False) != False: # ページ遷移の場合
          params["sort"] = request.GET["sort"]
          # モデルからデータを取得する
          results = SearchResult.objects.all()
          
          for result in results:
            d = {}
            d["title"] = result.title
            d["url"] = result.url
            d["thumbnail"] = result.thumbnail
            d["viewCount"] = result.viewCount

            params["result"].append(d)

        else:
          # 検索キーワードを受け取って検索する
          form = SearchForm(request.POST)
          params["word"] = request.GET["word"]
          params["form"] = form
          word = request.GET["word"] # 検索キーワード

          # 指定された条件で検索する -------------------
          sort = params["sort"]

          if sort == "関連性が高い順":
            searchfunc(word, "relevance") # 検索する
          elif sort == "投稿日時が新しい順": # いらない?
            searchfunc(word, "date") # 検索する
          elif sort == "評価の高い順": # いらない?
            searchfunc(word, "rating") # 検索する
          elif sort == "再生回数の多い順": # いらない?
            searchfunc(word, "viewCount") # 検索する

        # ページング処理 -----------
        page = request.GET.get("page", 1) # 現在のページ数を取得する(なければ1)
        # 1ページに表示するデータ数を指定する
        paginator = Paginator(params["result"], 10)
        try:
          results = paginator.page(page)
        except PageNotAnInteger:
          results = paginator.page(1)
        except EmptyPage:
          results = paginator.page(paginator.num_pages)
        params["result"] = results

  return render(request, "youtube_search.html", params)

# niconico --------------------------------------------------------------------------
def niconico_searchfunc(request):
  def searchfunc(word, sort): # 検索する関数
    REQUEST_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

    # クエリ文字列仕様
    query = {
        "q":word,
        "targets":"title,tags",
        "fields":"contentId,title,viewCounter,thumbnailUrl,description",
        "_sort":sort,
        "_context":"nico_jsonFilter",
        "_limit":50, # 取得する動画の数
    }

    # データベースに保存されている検索結果を削除する -----------
    SearchResult.objects.all().delete()

    # データを取得する
    responses = requests.get(REQUEST_URL, query).json()

    for i in range(len(responses["data"])):
      d = {} # 辞書型
      d["title"] = responses["data"][i]["title"]
      d["viewCounter"] = responses["data"][i]["viewCounter"]
      d["thumbnail"] = responses["data"][i]["thumbnailUrl"]
      d["url"] = "https://nico.ms/" + responses["data"][i]["contentId"]
      params["result"].append(d) # 検索結果を保存する -----------

      # 検索結果をデータベースに保存する -----------
      r = SearchResult(
        title=responses["data"][i]["title"],
        url="https://nico.ms/" + responses["data"][i]["contentId"],
        thumbnail=responses["data"][i]["thumbnailUrl"],
        viewCount=responses["data"][i]["viewCounter"]
      )
      r.save() # SearchResultモデルに追加する

  params = { # 渡すデータ
    "word": "",
    "form": None,
    "result": [],
    "sort": "再生回数の多い順"
  }

  if request.method == "POST": # フォームが送信されたとき
    # 並び替えのボタン(関連性が高い順など)が押されたとき
    if request.POST.get("sort", False) != False:
      if request.GET.get("word", False) == False: # 検索ワードが入っていないとき
        # エラー処理
        messages.error(request, "キーワードを入力してください")
      
      else: # 検索ワードが入っているとき
        if request.GET["word"] == "": # 検索ワードが入っていないとき
          # エラー処理
          messages.error(request, "キーワードを入力してください")
        else:
          sort = request.POST["sort"]
          word = request.GET["word"]
          params["sort"] = sort # テキストを変更する

          # 指定された条件で検索する -------------------
          if sort == "再生回数の多い順":
            searchfunc(word, "viewCounter") # 検索する
          elif sort == "マイリスト数・お気に入り数が多い順":
            searchfunc(word, "mylistCounter") # 検索する
          elif sort == "投稿日時が新しい順":
            searchfunc(word, "startTime") # 検索する
          elif sort == "コメント数の多い順":
            searchfunc(word, "commentCounter") # 検索する

          # ページング処理 -----------
          page = 1 # 1ページ目を表示するようにする --------

          # 1ページに表示するデータ数を指定する
          paginator = Paginator(params["result"], 10)
          try:
            results = paginator.page(page)
          except PageNotAnInteger:
            results = paginator.page(1)
          except EmptyPage:
            results = paginator.page(paginator.num_pages)
          params["result"] = results

    # 「マイリストに追加」ボタンが押されたとき、mylist_add.htmlに遷移する
    elif request.POST.get("title", False) != False:
      if not request.user.is_authenticated: # ログイン認証
        messages.error(request, "ログインしてください")
        return redirect("/siteUser/login")
      d = {}
      d["title"] = request.POST["title"]
      d["url"] = request.POST["url"]
      d["thumbnail"] = request.POST["thumbnail"]
      d["categories"] = VideoCategory.objects.filter(user=request.user).order_by("name").distinct()

      return render(request, "mylist_add.html", d)

    params["form"] = SearchForm()
  
  elif request.method == "GET":
    params["form"] = SearchForm()

    is_exist_word = request.GET.get("word", False)
    if is_exist_word != False: # 「検索」ボタンが押されたとき、ページ番号が異なるページから遷移したとき
      if request.GET["word"] == "": # 検索ワードが入っていないとき
        # エラー処理
        messages.error(request, "キーワードを入力してください")

      else:
        if request.GET.get("sort", False) != False: # ページ遷移の場合
          params["sort"] = request.GET["sort"]
          # モデルからデータを取得する
          results = SearchResult.objects.all()

          for result in results:
            d = {}
            d["title"] = result.title
            d["url"] = result.url
            d["thumbnail"] = result.thumbnail
            d["viewCounter"] = result.viewCount

            params["result"].append(d)

        else:
          # 検索キーワードを受け取って検索する
          form = SearchForm(request.POST)
          params["word"] = request.GET["word"]
          params["form"] = form
          word = request.GET["word"] # 検索キーワード

          # 指定された条件で検索する -------------------
          sort = params["sort"]
          if sort == "再生回数の多い順":
            searchfunc(word, "viewCounter") # 検索する
          elif sort == "マイリスト数・お気に入り数が多い順":
            searchfunc(word, "mylistCounter") # 検索する
          elif sort == "投稿日時が新しい順":
            searchfunc(word, "startTime") # 検索する
          elif sort == "コメント数の多い順":
            searchfunc(word, "commentCounter") # 検索する

        # ページング処理 -----------
        page = request.GET.get("page", 1) # 現在のページ数を取得する(なければ1)
        # 1ページに表示するデータ数を指定する
        paginator = Paginator(params["result"], 10)
        try:
          results = paginator.page(page)
        except PageNotAnInteger:
          results = paginator.page(1)
        except EmptyPage:
          results = paginator.page(paginator.num_pages)
        params["result"] = results

  return render(request, "niconico_search.html", params)

# マイリスト(カテゴリ一覧)
# @login_required
def mylistfunc(request):
  if not request.user.is_authenticated: # ログイン認証
        messages.error(request, "ログインしてください")
        return redirect("/siteUser/login")

  if request.method == "GET": # 最初に関数が呼ばれたとき
    # カテゴリを全て取得する(名前でソートする)
    categories = []
    for i in VideoCategory.objects.filter(user=request.user).order_by("name").distinct().values("name"):
      categories.append(i["name"])

    context = {
      "mylist": Video.objects.filter(user=request.user).order_by("-id"),
      "categories": categories
    }
    return render(request, "mylist.html", context)

  elif request.method == "POST":
    category_list = request.POST.getlist("check_delete")

    if request.POST.get("category_add", False) != False:
      # カテゴリを追加する
      category_add = request.POST["category_add"] # 追加するカテゴリ
        
      form = VideoCategoryReservationForm({
        "name":category_add,
        "user":request.user
      })

      if category_add == "": # カテゴリが入力されていないとき
        messages.error(request, "カテゴリを入力してください")

      elif form.is_valid() == True:
        # モデル「VideoCategory」に追加する
        vc = VideoCategory(
          name=category_add,
          user=request.user
        )
        vc.save() # VideoCategoryモデルに追加する
        messages.success(request,"カテゴリ「" + category_add + "」が追加されました")
      else: # 同じデータが既にあるとき
        messages.error(request, "カテゴリ「" + category_add + "」は既に存在します")

    # カテゴリが1つ以上選択されたとき
    elif category_list != []:
      for i in category_list:
        # VideoCategoryモデルから削除する
        v = VideoCategory.objects.filter(user=request.user).filter(name=i)
        v.delete()
        messages.success(request, "カテゴリ「" + i + "」を削除しました")

    else:
      # 削除するカテゴリが選択されなかったとき
      messages.error(request,"削除するカテゴリを選択してください")

    # カテゴリを全て取得する
    categories = []
    for i in VideoCategory.objects.filter(user=request.user).order_by("name").distinct().values("name"):
      categories.append(i["name"])

    context = {
      "mylist": Video.objects.filter(user=request.user).order_by("-id"),
      "categories": categories
    }

    return render(request, "mylist.html", context)

# マイリスト(カテゴリ別)
@login_required
def mylist_categoryfunc(request, pk):
  # pk: 選択したカテゴリの名前
  if request.method == "POST": # 削除する動画を選択したとき
    # 選択した動画を削除する
    category_name = request.POST.get("category_name")

    video_list = request.POST.getlist("check_delete")

    # 動画が1つ以上選択されたとき
    if video_list != []:
      for i in video_list:
        # string → dict
        i = ast.literal_eval(i)

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

  video_info = []
  for i in video:
    d = {}
    # タイトル
    title = str(i)
    d["title"] = title
    
    v = Video.objects.filter(user=request.user).filter(category__name=pk).filter(title=title)
    # URL
    d["url"] = v[0].url

    if "youtube" in d["url"]:
      d["type"] = "YouTube"
    elif "nico" in d["url"]:
      d["type"] = "ニコニコ動画"

    # サムネイル
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
  if request.method == "POST":
    d = {}
    if "category_add_button" in request.POST:
      # カテゴリを追加する
      category_add = request.POST["category_add"] # 追加するカテゴリ
        
      form = VideoCategoryReservationForm({
        "name":category_add,
        "user":request.user
      })

      if category_add == "": # カテゴリが入力されていないとき
        messages.error(request, "カテゴリを入力してください")

      elif form.is_valid() == True:
        # モデル「VideoCategory」に追加する
        vc = VideoCategory(
          name=category_add,
          user=request.user
        )
        vc.save() # VideoCategoryモデルに追加する
        messages.success(request,"カテゴリ「" + category_add + "」が追加されました")
      else: # 同じデータが既にあるとき
        messages.error(request, "カテゴリ「" + category_add + "」は既に存在します")

      d["title"] = request.POST["title"]
      d["url"] = request.POST["url"]
      d["thumbnail"] = request.POST["thumbnail"]
      d["categories"] = VideoCategory.objects.filter(user=request.user).order_by("name").distinct()

    elif "video_add_button" in request.POST:
      # 選択した動画をマイリストに追加 ---------------
      d["title"] = request.POST["title"]
      d["url"] = request.POST["url"]
      d["thumbnail"] = request.POST["thumbnail"]
      d["categories"] = VideoCategory.objects.filter(user=request.user).order_by("name").distinct()

      category_checked = False # カテゴリが1つ以上選択されていればTrue

      for key in request.POST:
        if(request.POST[key]=="on"):
          category_checked = True

          # 重複しているデータがあるか判定する
          form = VideoReservationForm({
            "url":request.POST["url"],
            "user":request.user,
            "category":VideoCategory.objects.filter(name=key)[0]
          })

          if form.is_valid() == True:
            # モデル「Video」に追加する ---------------
            v = Video(
              title=request.POST["title"],
              url=request.POST["url"],
              thumbnail=request.POST["thumbnail"],
              user=request.user,
              category=VideoCategory.objects.filter(name=key)[0]
            )
            v.save() # 「Video」モデルに追加する
            messages.success(request, request.POST["title"] + "をマイリスト(" + key + ")に追加しました")
          else: # 同じデータが既にあるとき
            messages.error(request, request.POST["title"] + "は既にマイリスト(" + key + ")に保存されています")

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

        # ログインしたらマイリストに遷移する
        return redirect("../../mylist")

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