from django.core.paginator import Paginator


def build_pagination_query(request, page_param='page'):
    query_params = request.GET.copy()
    query_params.pop(page_param, None)
    return query_params.urlencode()


def paginate_queryset(request, queryset, per_page=10, page_param='page'):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param)
    return {
        'page_obj': paginator.get_page(page_number),
        'paginator': paginator,
        'pagination_query': build_pagination_query(request, page_param),
    }


class PaginationMixin:
    paginate_by = 10
    page_kwarg = 'page'
    pagination_context_name = 'pagination_query'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.pagination_context_name] = build_pagination_query(self.request, self.page_kwarg)
        return context
