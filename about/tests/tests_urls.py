from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus


class AboutTemplateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.urls = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }

    def setUp(self):
        self.guest_client = Client()

    def test_noauth_access(self):
        """Проверка доступа к страницам About"""

        for url in AboutTemplateTests.urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'нет доступа к {url}'
                )

    def test_urls_uses_correct_template(self):
        """Проверка, что URL-адрес использует соответствующий шаблон."""

        for url, template in AboutTemplateTests.urls.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
