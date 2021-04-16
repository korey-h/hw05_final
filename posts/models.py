from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name="Название группы",
        help_text="Дайте название группе",
        max_length=200,
    )
    slug = models.SlugField(max_length=70, unique=True)
    description = models.TextField(max_length=150)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст сообщения",
        help_text="Введите текст для публикации.")
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group,
                              related_name="posts",
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              verbose_name="Группа",
                              help_text="Выберете группу для публикации")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField(
        verbose_name="Комментарий",
        help_text="Введите текст комментария.")
    created = models.DateTimeField("date creation", auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="comments")
    post = models.ForeignKey(Post,
                             related_name="comments",
                             on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following")
