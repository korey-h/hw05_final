import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Group, Post, User


class CreateFromFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Обо всём',
            slug='obo_vsem',
            description='тестовая группа'
        )

        cls.user = User.objects.create_user(username='user1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(CreateFromFormTests.user)
        cls.post_base = Post.objects.create(
            text='постоянное сообщение',
            author=cls.user,
        )
        cls.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_create_fr_web_form(self):
        """Проверка, что данные из формы создания поста
        сохраняются в базе данных"""

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
        im_direct = Post._meta.get_field('image').upload_to + uploaded.name
        test_post = {
            'text': 'отредактированный',
            'group': CreateFromFormTests.group.id,
            'image': uploaded}

        post_amount = Post.objects.count()
        self.authorized_client.post(
            reverse('new_post'),
            data=test_post,
            follow=True
        )
        post = Post.objects.latest('pub_date')

        self.assertEqual(Post.objects.count(), post_amount + 1,
                         'Пост не попал в базу данных')
        self.assertEqual(post.text, test_post['text'],
                         'Пост сохранился с неправильным текстом')
        self.assertEqual(post.group, CreateFromFormTests.group,
                         'Пост сохранился с неправильной группой')
        self.assertEqual(post.author, CreateFromFormTests.user,
                         'Пост сохранился с неправильным автором')
        self.assertEqual(post.image, im_direct, 'Изображение не сохранилось')

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
        redacted_post = Post.objects.latest('pub_date')
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
            f'{reverse("login")}?next={reverse("new_post")}'
        )
        self.assertEqual(
            amount_before,
            amount_after,
            'В базе нежданное прибавление постов'
        )

    def test_create_comment_f_form(self):
        data = {'text': 'юзверский комментарий'}
        url = reverse(
            'add_comment',
            kwargs={'username': CreateFromFormTests.user.username,
                    'post_id': CreateFromFormTests.post_base.id}
        )
        amount_before = Comment.objects.all().count()
        CreateFromFormTests.authorized_client.post(url, data, follow=True)
        amount_after = Comment.objects.all().count()
        self.assertEqual(amount_before + 1, amount_after,
                         'Комментарий не сохранился')
        comment = Comment.objects.latest('created')
        self.assertEqual(comment.text, data['text'])

    def test_noauth_not_able_comments(self):
        data = {'text': 'тестовый комментарий'}
        url = reverse(
            'add_comment',
            kwargs={'username': CreateFromFormTests.user.username,
                    'post_id': CreateFromFormTests.post_base.id}
        )
        amount_before = Comment.objects.all().count()
        CreateFromFormTests.guest_client.post(url, data, follow=True)
        amount_after = Comment.objects.all().count()
        self.assertEqual(
            amount_before,
            amount_after,
            'Неавторизованный пользователь смог добавить комментарий')
