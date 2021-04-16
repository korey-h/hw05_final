from django.test import TestCase
from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='TestUser')

        cls.post = Post.objects.create(
            text='тестовая запись 12345',
            author=cls.user
        )

        cls.group = Group.objects.create(
            title='Обо всём',
            slug='obo_vsem',
            description='тестовая группа'
        )

    def test_text_labels(self):
        post = PostModelTest.post
        verbose = post._meta.get_field('text').verbose_name
        h_text = post._meta.get_field('text').help_text
        title = str(post)
        expect_title = PostModelTest.post.text[:15]

        self.assertEquals(verbose, 'Текст сообщения')
        self.assertEquals(h_text, 'Введите текст для публикации.')
        self.assertEquals(title, expect_title)

    def test_group_labels(self):
        group = PostModelTest.group
        verbose = group._meta.get_field('title').verbose_name
        h_text = group._meta.get_field('title').help_text
        title = str(group)
        expect_title = PostModelTest.group.title

        self.assertEquals(verbose, 'Название группы')
        self.assertEquals(h_text, 'Дайте название группе')
        self.assertEquals(title, expect_title)
