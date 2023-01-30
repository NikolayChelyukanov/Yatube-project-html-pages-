from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utilis import page_context


@cache_page(20, key_prefix="index_page")
def index(request):
    page_obj = page_context(Post.objects.all(), request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = page_context(group.posts.all(), request)
    context = {'page_obj': page_obj, 'group': group}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    page_obj = page_context(Post.objects.filter(author=author), request)
    if request.user.is_authenticated and Follow.objects.filter(
            author=author, user=request.user).exists():
        following = True
        context = {
            'page_obj': page_obj,
            'author': author,
            'following': following
        }
        return render(request, 'posts/profile.html', context)
    following = False
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        context = {'form': form, 'is_edit': False}
        post.save()
        return redirect('posts:profile', post.author)
    context = {'form': form, 'is_edit': False}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {'form': form, 'is_edit': True}
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = page_context(
        Post.objects.filter(author__following__user=request.user), request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not Follow.objects.filter(
                user=request.user, author=author).exists():
            Follow.objects.create(user=request.user, author=author)
            return redirect('posts:profile', username=username)
        Follow.objects.get(user=request.user, author=author)
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
