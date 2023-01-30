from django.core.paginator import Paginator

FIRST_PAGE_POSTS = 10


def page_context(posts, request):
    paginator = Paginator(posts, FIRST_PAGE_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
