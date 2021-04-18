from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class CreateFromFormTests(TestCase):

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
        cls.authorized_client.force_login(CreateFromFormTests.user)

    def test_post_create_fr_web_form(self):
        """Проверка, что данные их формы создания поста
        сохраняются в базе данных"""

        post_amount = Post.objects.count()
        test_post = {
            'text': 'отредактированный',
            'group': CreateFromFormTests.group.id}

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
            CreateFromFormTests.group,
            'Пост сохранился с неправильной группой'
        )
        self.assertEqual(
            post.author,
            CreateFromFormTests.user,
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
            f'{reverse("login")}?next={reverse("new_post")}'
        )
        self.assertEqual(
            amount_before,
            amount_after,
            'В базе нежданное прибавление постов'
        )

    def test_image_saved_f_form(self):
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
        form_data = {
            'group': self.group.id,
            'text': 'особая запись',
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )

        post = Post.objects.get(text=form_data['text'])
        im_direct = post._meta.get_field('image').upload_to + uploaded.name
        self.assertEqual(post.image, im_direct, 'Изображение не сохранилось')
