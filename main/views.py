from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Category, Product, Size
from django.db.models import Q


class IndexView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = None
        return context


    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)


class CatalogView(TemplateView):
    template = 'main/base.html'

    FILTER_MAPPING = {
        'color': lambda queryset, value: queryset.filter(color__iexact=value),
        'min_price': lambda queryset, value: queryset.filter(price_gte=value),
        'max_price': lambda queryset, value: queryset.filter(price_lte=value),
        'size': lambda queryset, value: queryset.filter(product_size__size__name=value),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        products = Product.objects.all().order_by('-created_at')
        current_category = None

        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            products = products.filter(category=current_category)


        query = self.request.Get.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.Get.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''

        filter_params['q'] = query or ''

        context.update({
            'categories': categories,
            'products': products,
            'current_category': category_slug,
            'filter_params': filter_params,
            'sizes': Size.objects.all(),
            'search_query': query or ''
        })

        if self.request.Get.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.Get.get('reset_serch') == 'true':
            context['reset_search'] = True

        return context


    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            template = 'main/filter_modal.html' if request.GET.get('show_filters') == 'true' else 'main/catalog.html'
            return TemplateResponse(request, template, context)
        return TemplateResponse(request, self.template_name, context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['categories'] = Category.objects.all()
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        context['current_category'] = product.category.slug
        return context


    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.header.get('HX_Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        raise TemplateResponse(request, self.template_name, context)
