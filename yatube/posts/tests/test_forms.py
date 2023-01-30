import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Проверка создания записи в БД при создании нового поста"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст новый'}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

    def test_post_edit(self):
        """Проверка изменения поста в БД при редактировании"""
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст поста',
            group=self.group,
        )
        posts_count = Post.objects.count()
        post_exist = Post.objects.get(pk=post.pk)
        form_data = {'text': 'Отредактированный в форме текст'}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        post.refresh_from_db()
        self.assertNotEqual(post.text, post_exist.text)

    def test_post_create_with_picture(self):
        ("""Проверка создания записи в БД"""
         """при создании нового поста c картинкой""")
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст поста с картинкой',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_comment_appear_at_post_details(self):
        """После успешной отправки комментарий появляется на странице поста"""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст поста',
            group=self.group,
        )
        form_data = {'text': 'Комментарий к посту'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.pk}))
        self.assertEqual(len(response.context['comments']), comments_count + 1)
