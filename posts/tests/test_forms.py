from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Follow, Post, User


class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Обо всём',
            slug='obo_vsem',
            description='тестовая группа'
        )

        cls.user = User.objects.create_user(username='user1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateFormTests.user)

    def test_post_create_fr_web_form(self):
        """Проверка, что данные их формы создания поста
        сохраняются в базе данных"""

        post_amount = Post.objects.count()
        test_post = {
            'text': 'отредактированный',
            'group': PostCreateFormTests.group.id}

        self.authorized_client.post(
            reverse('new_post'),
            data=test_post,
            follow=True
        )

        self.assertEqual(
            Post.objects.count(),
            post_amount + 1,
            'Пост не попал в базу данных'
        )

        post = Post.objects.last()
        self.assertEqual(
            post.text,
            test_post['text'],
            'Пост сохранился с неправильным текстом'
        )

        self.assertEqual(
            post.group,
            PostCreateFormTests.group,
            'Пост сохранился с неправильной группой'
        )
        self.assertEqual(
            post.author,
            PostCreateFormTests.user,
            'Пост сохранился с неправильным автором'
        )

    def test_post_edit_fr_web_form(self):
        """Проверка, что данные из формы
        сохраняются в базе данных после редактирвания поста"""

        group_changed = Group.objects.create(
            title='one',
            slug='one',
            description='группа на замену'
        )

        new_post = Post.objects.create(
            text='тестовая запись 12345',
            author=self.user,
        )

        test_data = {'text': 'отредактированный', 'group': group_changed.id}

        self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': new_post.author.username,
                'post_id': new_post.id}
            ),
            data=test_data,
            follow=True
        )
        redacted_post = Post.objects.last()
        self.assertEqual(
            test_data['text'],
            redacted_post.text,
            'Текст сообщения не отредактировался'
        )
        self.assertEqual(
            test_data['group'],
            redacted_post.group.id,
            'Группа не отредактировалась'
        )

    def test_noauth_no_create_post(self):
        test_post = {'text': 'неправильный пост'}
        guest_client = Client()
        amount_before = Post.objects.count()
        responce = guest_client.post(
            reverse('new_post'),
            data=test_post,
            follow=True
        )
        amount_after = Post.objects.count()
        self.assertRedirects(
            responce,
            f'/auth/login/?next={reverse("new_post")}'
        )
        self.assertEqual(
            amount_before,
            amount_after,
            'В базе нежданное прибавление постов'
        )

    def test_follow_and_unfollow(self):
        """Проверка, что авторизованный пользователь
        может подписываться и отписываться от автора"""

        follower_user = User.objects.create_user(username='follower')
        authorized_client = Client()
        authorized_client.force_login(follower_user)
        amount_nofollow = Follow.objects.count()
        authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': PostCreateFormTests.user.username})
        )
        amount_follow = Follow.objects.count()
        self.assertEqual(amount_nofollow + 1, amount_follow,
                         "Подписка не сохранилась в базе")
        authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': PostCreateFormTests.user.username})
        )
        amount_unfollow = Follow.objects.count()
        self.assertEqual(amount_unfollow, amount_nofollow,
                         "Подписка не удалилась из базы")

    def test_post_pass_on_follower_page(self):
        """Проверка, что пост автора появляется
            только на странице у его подписчика"""

        author_post = Post.objects.create(
            text='авторская запись',
            author=PostCreateFormTests.user
        )
        follower_user = User.objects.create_user(username='follower')
        nofollower_user = User.objects.create_user(username='hater')
        authorized_client = Client()
        authorized_client.force_login(follower_user)
        authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': PostCreateFormTests.user.username})
        )
        response = authorized_client.get(reverse('follow_index'))
        follower_post = response.context.get('page')[0]
        self.assertEqual(follower_post, author_post)

        authorized_client.force_login(nofollower_user)
        response = authorized_client.get(reverse('follow_index'))
        unfollower_posts = response.context.get('page')
        self.assertEqual(len(unfollower_posts), 0)
