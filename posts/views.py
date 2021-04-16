from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from http import HTTPStatus

from .forms import CommentForm, PostForm
from .models import Group, Follow, Post, User
from yatube.settings import POSTS_ON_PAGE


def index(request):
    post_page = Post.objects.all()
    paginator = Paginator(post_page, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.all()
    paginator = Paginator(group_posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


@login_required
def new_post(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new = form.save(commit=False)
            new.author = request.user
            new.save()
            return redirect('index')
    return render(request, 'new_post.html', {'form': form, 'is_edit': False})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    all_posts = author.posts.all()
    paginator = Paginator(all_posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    is_following = False
    if author != request.user:
        if author.following.filter(user=request.user):
            is_following = True

    return render(
        request,
        'profile.html',
        {'page': page, 'author': author, 'is_following': is_following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    is_following = False
    if author != request.user:
        if author.following.filter(user=request.user):
            is_following = True

    return render(
        request,
        'post.html',
        {'post': post, 'author': author, 'comments': comments,
         "form": form, 'is_following': is_following}
    )


@login_required
def post_edit(request, username, post_id):
    if username != request.user.username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post.save()
            return redirect('post', username=username, post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    return render(request, 'new_post.html', {'form': form, 'is_edit': True})


def page_not_found(request, exception=None):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=HTTPStatus.NOT_FOUND
    )


def server_error(request):
    return render(
        request,
        "misc/500.html",
        status=HTTPStatus.INTERNAL_SERVER_ERROR
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            new = form.save(commit=False)
            new.author = request.user
            new.post = post
            new.save()
            return redirect("post", username=username, post_id=post_id)
    return redirect("post", username=username, post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    post_page = Post.objects.filter(author__following__user=user)
    paginator = Paginator(post_page, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        if not author.following.filter(user=request.user):
            follower = Follow.objects.create(author=author, user=user)
            follower.save()

    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        if author.following.filter(user=request.user):
            follower = Follow.objects.filter(author=author, user=user)
            follower.delete()

    return redirect("profile", username=username)
