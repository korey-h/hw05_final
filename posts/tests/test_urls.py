from django.core.cache.backends import locmem
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus
from posts.models import Comment, Group, Post, User


class AccessURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Обо всём',
            slug='obo_vsem',
            description='тестовая группа'
        )
        cls.user = User.objects.create_user(username='user1')
        cls.post = Post.objects.create(
            text='тестовая запись 12345',
            author=cls.user
        )

        cls.test_urls = {
            reverse('index'): 'index.html',
            reverse('group',
                    kwargs={'slug': cls.group.slug}
                    ): 'group.html',
            reverse('new_post'): 'new_post.html',
            reverse('post_edit',
                    kwargs={'username': cls.user.username,
                            'post_id': cls.post.id
                            }
                    ): 'new_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(AccessURLTests.user)

    def test_homepage(self):
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_access(self):
        """Проверка доступа авторизованного пользователя ко всем страницам"""

        for url in AccessURLTests.test_urls.keys():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'ошибка доступа к странице {url}'
                )

    def test_noauth_access(self):
        """Проверка доступа неавторизованного пользователя ко всем страницам"""

        common_urls = (
            reverse('index'),
            reverse('group', kwargs={'slug': AccessURLTests.group.slug}),
            reverse('profile',
                    kwargs={'username': AccessURLTests.user.username}),
            reverse('post',
                    kwargs={'username': AccessURLTests.user.username,
                            'post_id': AccessURLTests.post.id}),
        )

        auth_urls = (
            reverse('new_post'),
            reverse('post_edit',
                    kwargs={'username': AccessURLTests.user.username,
                            'post_id': AccessURLTests.post.id}
                    ),
        )

        for url in common_urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'нет доступа к {url}'
                )

        for url in auth_urls:
            with self.subTest():
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_post_edit_access(self):
        """Проверка, что пост редактировать может только автор"""

        url = reverse(
            'post_edit',
            kwargs={'username': AccessURLTests.user.username,
                    'post_id': AccessURLTests.post.id})
        url_redir = reverse(
            'post',
            kwargs={'username': AccessURLTests.user.username,
                    'post_id': AccessURLTests.post.id})

        authorized_client_viewer = Client()
        user_viewer = User.objects.create_user(username='user2')
        authorized_client_viewer.force_login(user_viewer)
        response = authorized_client_viewer.post(url, {'text': 'any'},
                                                 follow=True)
        self.assertRedirects(response, url_redir)

        response = self.authorized_client.post(url, {'text': 'any'},
                                               follow=True)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            f'ошибка доступа к странице {url}'
        )

    def test_urls_uses_correct_template(self):
        """Проверка, что URL-адрес использует соответствующий шаблон."""

        for url, template in AccessURLTests.test_urls.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_responce_if_url_notfound(self):
        url = reverse('index') + 'error'
        response = self.authorized_client.get(url, follow=True)
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            f'не выводится страница об ошибке 404 для {url}'
        )

    def test_index_page_saved_in_cache(self):  # требует доработки!
        self.authorized_client.get(reverse('index'), data={'page': 1})
        keys2 = []
        for item in locmem._caches[''].keys():
            if 'index_page' in item:
                keys2.append(item)
        self.assertNotEqual(0, len(keys2), 'страница не попала в кэш')

    def test_noauth_not_able_comments(self):
        data = {'text': 'тестовый комментарий'}
        url = reverse(
            'add_comment',
            kwargs={'username': AccessURLTests.user.username,
                    'post_id': AccessURLTests.post.id}
        )
        amount_before = Comment.objects.all().count()
        self.guest_client.post(url, data, follow=True)
        amount_after = Comment.objects.all().count()
        self.assertEqual(
            amount_before,
            amount_after,
            'Неавторизованный пользователь смог добавить комментарий')
