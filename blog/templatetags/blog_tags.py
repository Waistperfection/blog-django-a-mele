from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.db.models import QuerySet

import markdown

from ..models import Post

register = template.Library()


@register.simple_tag
def total_posts() -> int:
    return Post.published.count()


@register.inclusion_tag('blog/post/lastest_posts.html')
def show_lastest_posts(count: int = 3) -> dict[str: QuerySet]:
    lastest_posts = Post.published.order_by('-publish')[:count]
    return {'lastest_posts': lastest_posts}


@register.simple_tag
def get_most_commented_posts(count: int = 5) -> QuerySet:
    most_commented = Post.published.annotate(
        total_comments=Count('comments')
        ).order_by('-total_comments', 'publish')[:count]
    return most_commented


@register.filter(name='markdown')
def markdown_format(text: str) -> str:
    return mark_safe(markdown.markdown(text))
