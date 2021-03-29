from django import forms
from .models import SiteUser, Video, VideoCategory
import re
from django.core.exceptions import ObjectDoesNotExist

# youtube,niconico検索
class SearchForm(forms.Form):
  word = forms.CharField(label="", max_length=100,
    widget=forms.TextInput(attrs={"name":"search","placeholder":"キーワードを入力"}))

# マイリストへの動画の追加に使う
# VideoReservationForm使っててこっちは使ってない...?
class MyVideo(forms.ModelForm):
    class Meta:
        model = Video
        # 使用するフィールド
        # fields = ('title', 'url', 'thumbnail')
        fields = ('url', 'category')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


    def clean(self):
        # 複合ユニーク制約をバリデーション
        cleaned_data = super(MyVideo, self).clean()
        url = self.cleaned_data.get("url")
        user = self.user
        category = self.cleaned_data.get("category")

        if Video.check_myvideo_unique(url, user, category):
            raise forms.ValidationError("")

# VideoCategoryのデータの重複を防ぐ
class VideoCategoryReservationForm(forms.ModelForm):
    class Meta:
        model = VideoCategory
        fields = ["name", "user"]

# Videoのデータの重複を防ぐ
class VideoReservationForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["url", "user", "category"]

# ログイン認証
class SiteUserRegisterForm(forms.ModelForm):
    class Meta:
        model = SiteUser

        fields = (
            "username",
            "email",
            "password",
        )

        labels = {
            "username": "ユーザ名",
            "email": "メールアドレス",
            "password": "パスワード",
        }

        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "4文字以上で入力してください"}),
            "password": forms.PasswordInput(),
        }

    password2 = forms.CharField(
        label="確認用パスワード", required=True, widget=forms.PasswordInput(),
    )

    def clean_username(self):

        username = self.cleaned_data["username"]
        if len(username) < 4:
            raise forms.ValidationError("4文字以上で入力してください")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        return password

    def clean(self):

        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password != password2:
            raise forms.ValidationError("パスワードと確認用パスワードが一致しません")
        # ユニーク制約を自動でバリデーション
        super().clean()


class SiteUserLoginForm(forms.Form):

    email = forms.EmailField(label="メールアドレス", required=False)
    password = forms.CharField(
        label="パスワード", required=False, widget=forms.PasswordInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_user_cache = None

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        try:
            site_user = SiteUser.objects.get(email=email)
        except ObjectDoesNotExist:
            raise forms.ValidationError("メールアドレスかパスワードが間違っています")
        if not site_user.check_password(password):
            raise forms.ValidationError("メールアドレスかパスワードが間違っています")

        self.site_user_cache = site_user

    def get_site_user(self):
        return self.site_user_cache