import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


class BrowseView(TemplateView):
    template_name = 'web/browse.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        code_directory = os.path.realpath(settings.CODE_DIRECTORY) + os.path.sep
        absolute_path = self.request.GET.get('path')
        if not absolute_path:
            return redirect(reverse('web:browse') + '?path=/')
        if not absolute_path.startswith('/'):
            raise Http404
        absolute_path = '.' + absolute_path
        absolute_path = os.path.join(settings.CODE_DIRECTORY, absolute_path)
        absolute_path = os.path.realpath(absolute_path) + os.path.sep

        if not absolute_path.startswith(code_directory):
            raise Http404

        if not os.path.exists(absolute_path):
            raise Http404

        if not os.path.isdir(absolute_path):
            raise Http404

        relative_path = '/' + absolute_path[len(code_directory):]

        parent_directory = os.path.realpath(os.path.join(absolute_path, os.path.pardir)) + os.path.sep
        parent_directory = '/' + parent_directory[len(code_directory):]

        directories = []
        files = []
        everything = os.listdir(absolute_path)
        for f in everything:
            path = os.path.join(absolute_path, f)
            if os.path.isdir(path):
                directories.append(f)
            else:
                files.append(f)

        context['files'] = sorted(files)
        context['directories'] = sorted(directories)
        context['relative_path'] = relative_path
        context['parent_directory'] = parent_directory
        return self.render_to_response(context)


class AnnotateView(TemplateView):
    template_name = 'web/annotate.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        code_directory = os.path.realpath(settings.CODE_DIRECTORY) + os.path.sep
        absolute_path = self.request.GET.get('path')
        if not absolute_path:
            return redirect(reverse('web:browse') + '?path=/')
        if not absolute_path.startswith('/'):
            raise Http404
        absolute_path = '.' + absolute_path
        absolute_path = os.path.join(settings.CODE_DIRECTORY, absolute_path)
        absolute_path = os.path.realpath(absolute_path)

        if not absolute_path.startswith(code_directory):
            raise Http404

        if not os.path.exists(absolute_path):
            raise Http404

        if not os.path.isfile(absolute_path):
            raise Http404

        context['code'] = absolute_path

        with open(absolute_path) as f:
            code = f.read()
        code = highlight(code, PythonLexer(), HtmlFormatter(linenos='inline', linespans='line'))

        context['code'] = code
        context['css'] = HtmlFormatter().get_style_defs('.highlight')
        return self.render_to_response(context)
