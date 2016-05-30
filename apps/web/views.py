from django.views.generic import TemplateView


class BrowseView(TemplateView):
    template_name = 'web/browse.html'

    def get_context_data(self, **kwargs):
        context = super(BrowseView, self).get_context_data(**kwargs)
        return context


class AnnotateView(TemplateView):
    template_name = 'web/annotate.html'

    def get_context_data(self, **kwargs):
        context = super(AnnotateView, self).get_context_data(**kwargs)
        return context
