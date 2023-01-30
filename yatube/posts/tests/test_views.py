import shutil
import tempfile

from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post
from ..utilis import FIRST_PAGE_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.user = User.objects.create(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-another-slug',
            description='Тестовое описание группы 2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}):
                        'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        self.assertEqual(response.context['author'], self.author)
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertFalse(response.context['following'])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context['post'], self.post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertFalse(response.context['is_edit'])

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])

    def test_created_post_show_at_correct_pages(self):
        ("""Созданный пост отобразился на главной странице, на странице группы,
        в профиле пользователя.""")
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username})
        ]
        for url in url_pages:
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_created_post_not_at_another_group_page(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_created_post_with_picture_show_at_correct_pages(self):
        ("""Созданный пост с картинкой отобразился на главной странице,"""
         """на странице группы, в профиле пользователя, странице поста.""")
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст поста c картинкой',
            group=self.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=small_gif,
                content_type='image/gif')
        )
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username})
        ]
        for url in url_pages:
            response = self.client.get(url)
            self.assertEqual(response.context['page_obj'][0].image, post.image)
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.pk}))
        self.assertEqual(response.context['post'].image, post.image)

    def test_autorized_user_can_comment_posts(self):
        """Комментировать посты может только авторизованный пользователь"""
        response = self.client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_cache_on_index_page(self):
        """Проверка кэширования на главной странице"""
        response = self.authorized_client.get(reverse('posts:index'))
        cached_response_content = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        cached_content_after_delete = response.content
        self.assertEqual(cached_response_content, cached_content_after_delete)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        content_afte_cache_clear = response.content
        self.assertNotEqual(cached_response_content, content_afte_cache_clear)

    def test_authorized_user_can_follow_author(self):
        ("""Авторизованный пользователь может подписываться"""
         """ на других пользователей""")
        follow_count = Follow.objects.count()
        self.authorized_client_2.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_authorized_user_can_unfollow_author(self):
        ("""Авторизованный пользователь может удалять из подписок"""
         """ других пользователей""")
        Follow.objects.create(user=self.user, author=self.author)
        follow_count = Follow.objects.count()
        self.authorized_client_2.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_posts_appear_at_user_follow_page(self):
        """Проверка появления записей в ленте тех, кто подписан."""
        post = Post.objects.create(
            author=self.author,
            text="Текст нового поста")
        Follow.objects.create(
            user=self.user,
            author=self.author)
        response = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_follow_posts_not_appear_at_other_users_follow_page(self):
        """Проверка отсутствия новой записей в ленте тех, кто не подписан."""
        post = Post.objects.create(
            author=self.author,
            text="Текст нового поста")
        response = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)


class PaginatorViewsTest(TestCase):
    TOTAL_POSTS = FIRST_PAGE_POSTS + 1
    SECOND_PAGE_POSTS = TOTAL_POSTS - FIRST_PAGE_POSTS

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                text=f'Пост #{i}',
                author=cls.author,
                group=cls.group
            )
            for i in range(cls.TOTAL_POSTS)
        ]
        Post.objects.bulk_create(cls.posts)

    def test_paginator_on_pages(self):
        """Проверка пагинации на страницах."""
        cache.clear()
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username})
        ]
        for responce in url_pages:
            with self.subTest(responce=responce):
                self.assertEqual(len(self.client.get(
                    responce).context.get('page_obj')), FIRST_PAGE_POSTS)
                self.assertEqual(len(self.client.get(
                    responce + '?page=2').context.get('page_obj')),
                    self.SECOND_PAGE_POSTS)
