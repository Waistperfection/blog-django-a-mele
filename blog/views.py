# django
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.http import HttpRequest, HttpResponse
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery,\
    SearchRank, TrigramSimilarity
# libs
from taggit.models import Tag
# user
from mysite.settings import EMAIL_HOST_USER
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post


def post_list(request: HttpRequest, tag_slug: str = None) -> HttpResponse:
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts,
                   'tag': tag})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_detail(request: HttpRequest,
                year: int,
                month: int,
                day: int,
                post: str) -> HttpResponse:

    post = get_object_or_404(Post,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             status=Post.Status.PUBLISHED)  # .select_relates('comments')

    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = (Post.published.filter(tags__in=post_tags_ids)
                     .exclude(id=post.id))
    similar_posts = (similar_posts.annotate(same_tags=Count('tags'))
                     .order_by('-same_tags', '-publish')[:4])
    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'similar_posts': similar_posts})


def post_share(request: HttpRequest, post_id: int) -> HttpResponse:

    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)

    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{form_data['name']} recommends for you {post.title}"
            message = f"Read {post.title} at {post_url}\n\n"\
                      f"{form_data['name']}\'s comments: {form_data['comments']}"
            send_mail(subject, message, EMAIL_HOST_USER, [form_data['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})


def post_search(request: HttpRequest):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
# 1st variant
            # results = Post.published.annotate(
            #     search=SearchVector('title', 'body'),
            #     ).filter(search=query)
# 2nd variant
            # search_vector = SearchVector('title', weight='A') + \
            #     SearchVector('body', weight='B')
            # search_query = SearchQuery(query)
            # results = Post.published.annotate(
            #     search=search_vector,
            #     rank=SearchRank(search_vector, search_query)
            # ).filter(rank__gte=0.1).order_by('-rank')
            # print(search_query.__dict__)
# 3d variant
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})
