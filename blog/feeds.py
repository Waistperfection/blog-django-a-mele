from datetime import datetime
import markdown
from django.db.models import QuerySet
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import Post


class LatestPostsFeed(Feed):
    title = 'My blog'
    link = reverse_lazy('blog:post_list')
    description = 'New posts of my blog.'

    def items(self) -> QuerySet:
        return Post.published.all()[:5]

    def item_title(self, item: Post) -> str:
        return item.title

    def item_description(self, item: Post) -> str:
        return truncatewords_html(markdown.markdown(item.body), 30)

    def item_pubdate(self, item: Post) -> datetime:
        return item.publish
