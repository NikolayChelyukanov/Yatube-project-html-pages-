from django.core.paginator import Paginator
from django.conf import settings


def get_page_obj(posts, request):
    paginator = Paginator(posts, settings.FIRST_PAGE_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
