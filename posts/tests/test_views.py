import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache.backends import locmem
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post, User
from yatube.settings import POSTS_ON_PAGE


class PageTemplateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group_base = Group.objects.create(
            title='Обо всём',
            slug='obo_vsem',
            description='тестовая группа'
        )
        cls.group_utility = Group.objects.create(
            title='тестовая',
            slug='test_gr',
            description='второй тест'
        )
        cls.user = User.objects.create_user(username='user1')
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=test_gif,
            content_type='image/gif'
        )

        cls.post_base = Post.objects.create(
            text='тестовая запись 12345',
            author=PageTemplateTests.user,
            group=PageTemplateTests.group_base,
            image=uploaded,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PageTemplateTests.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def compare_w_base(self, context):
        if 'page' in context:
            test_object = context['page'][0]
        else:
            test_object = context['post']

        post_base = PageTemplateTests.post_base
        self.assertEqual(test_object.author, post_base.author)
        self.assertEqual(test_object.text, post_base.text)
        self.assertEqual(test_object.group, post_base.group)
        self.assertEqual(
            test_object.image,
            post_base.image,
            'на страницу не передается изображение'
        )

    def test_pages_use_correct_template(self):
        test_urls = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group',
                kwargs={'slug': PageTemplateTests.group_base.slug}),
            'new_post.html': reverse('new_post'),
        }

        for template, url in test_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_start_page_shows_correct_context(self):
        """Проверка, что шаблон главной страницы сформирован с
        правильным контекстом."""

        response = self.authorized_client.get(reverse('index'))
        self.compare_w_base(response.context)

    def test_group_page_shows_correct_context(self):
        """Проверка. Шаблон страницы группы сформирован
        с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('group',
                    kwargs={'slug': PageTemplateTests.group_base.slug})
        )
        group_title = response.context['group'].title
        title_expected = PageTemplateTests.group_base.title
        self.assertEqual(group_title, title_expected)
        self.compare_w_base(response.context)

    def test_post_page_shows_correct_context(self):
        """Шаблон страницы создания поста
        сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('new_post'))
        in_form = response.context['form']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for name, field_type in form_fields.items():
            with self.subTest():
                self.assertIsInstance(
                    in_form.fields[name], field_type)

    def test_group_post_shows_correct(self):
        """Пост для группы публикуется только
        в этой группе """

        responce = self.authorized_client.get(
            reverse(
                'group',
                kwargs={'slug': PageTemplateTests.group_utility.slug})
        )
        posts_page = responce.context.get('page').object_list
        self.assertFalse(posts_page, 'В группе есть записи не из этой группы')

    def test_profile_page_show_correct_context(self):
        """Проверка, что шаблоны страниц пользователя сформированы с
        правильным контекстом."""

        urls = (
            reverse('post',
                    kwargs={'username': PageTemplateTests.user.username,
                            'post_id': PageTemplateTests.post_base.id}),
            reverse('profile',
                    kwargs={'username': PageTemplateTests.user.username})
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.compare_w_base(response.context)

    def test_image_used_on_pages(self):
        test_urls = (
            reverse('index'),
            reverse('group',
                    kwargs={'slug': PageTemplateTests.group_base.slug}),
            reverse('profile',
                    kwargs={'username': PageTemplateTests.user}),
            reverse('post',
                    kwargs={'username': PageTemplateTests.user,
                            'post_id': PageTemplateTests.post_base.id})
        )
        for url in test_urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.compare_w_base(response.context)

    def test_index_page_saved_in_cache(self):
        """Проверка кэширования страниц"""

        url = reverse('index')
        response = self.authorized_client.get(url)
        posts_before = response.context.get('page').object_list
        new = Post.objects.create(text='new запись',
                                  author=PageTemplateTests.user)
        response = self.authorized_client.get(url)
        posts_after = response.context.get('page').object_list
        self.assertEqual(posts_before[0], posts_after[0],
                         'страница не сохраняется в кэш')
        locmem._caches.clear()
        response = self.authorized_client.get(url)
        posts_update = response.context.get('page').object_list
        self.assertEqual(new, posts_update[0],
                         'страница не обновилась')

    def test_post_pass_on_follower_page(self):
        """Проверка, что пост автора появляется
        на странице у его подписчика"""

        follower_user = User.objects.create_user(username='follower')
        authorized_client = Client()
        authorized_client.force_login(follower_user)
        Follow.objects.create(author=PageTemplateTests.user,
                              user=follower_user)
        response = authorized_client.get(reverse('follow_index'))
        self.compare_w_base(response.context)

    def test_no_post_on_not_following_user_page(self):
        """Проверка, что пост автора непоявляется
        на странице у не подписанного на него пользователя"""

        nofollower_user = User.objects.create_user(username='hater')
        authorized_client = Client()
        authorized_client.force_login(nofollower_user)
        response = authorized_client.get(reverse('follow_index'))
        unfollower_posts = response.context.get('page')
        self.assertEqual(
            len(unfollower_posts),
            0,
            'На странице есть пост автора, на которого нет подписки')

    def test_make_follow(self):
        """Проверка, что авторизованный пользователь
        может подписываться на автора"""

        follower_user = User.objects.create_user(username='follower')
        authorized_client = Client()
        authorized_client.force_login(follower_user)
        authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': PageTemplateTests.user.username})
        )
        following = Follow.objects.filter(author=PageTemplateTests.user).last()
        self.assertEqual(follower_user, following.user,
                         'в базу сохранился неправильный подписчик')
        self.assertEqual(PageTemplateTests.user, following.author,
                         'в базу сохранился неправильный автор')

    def test_make_unfollow(self):
        follower_user = User.objects.create_user(username='follower')
        authorized_client = Client()
        authorized_client.force_login(follower_user)
        Follow.objects.create(author=PageTemplateTests.user,
                              user=follower_user)
        amount_before = Follow.objects.count()
        authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': PageTemplateTests.user.username})
        )
        amount_after = Follow.objects.count()
        self.assertEqual(amount_after, amount_before - 1,
                         "Подписка не удалилась из базы")


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        cls.user = User.objects.create_user(username='user1')
        for num in range(1, 14):
            text = f'Тестовая запись № {num}.'
            Post.objects.create(text=text, author=cls.user)

    def test_first_page_containse_ten_records(self):
        response = PaginatorViewsTest.client.get(reverse('index'))
        page_content = response.context.get('page').object_list
        self.assertEqual(len(page_content), POSTS_ON_PAGE)

    def test_second_page_containse_three_records(self):
        response = PaginatorViewsTest.client.get(reverse('index') + '?page=2')
        page_content = response.context.get('page').object_list
        self.assertEqual(len(page_content), 3)
