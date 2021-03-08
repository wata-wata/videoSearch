from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _

# 保存する動画の情報
class Video(models.Model):
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=300)
    thumbnail = models.CharField(max_length=300)
    # レシピを保存するユーザーの情報
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,)

    class Meta:
        constraints = [
            # ユニーク制約
            models.UniqueConstraint(
                fields=("url", "user"),
                name="myvideo_unique"
            )
        ]

    @classmethod
    def check_myvideo_unique(cls, url, user) -> bool:
        """同じデータががすでにDBに登録されているどうかを判定します

        登録されていたらTrue, されていなかったらFalseを返します。
        """
        return cls.objects.filter(url=url, user=user).exists()

    # クラスオブジェクトを文字列で返すメソッド
    def __str__(self):
        return self.title

# ログイン認証
class SiteUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

# ログイン認証
class SiteUser(AbstractUser):
    class Meta(object):
        db_table = "site_user"
        verbose_name = "ユーザー"
        verbose_name_plural = _("ユーザー")

    username = models.CharField(_("username"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)

    objects = SiteUserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []
