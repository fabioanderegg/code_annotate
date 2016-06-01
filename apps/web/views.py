import os
from fnmatch import fnmatch
from operator import itemgetter

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView, CreateView

from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters.html import HtmlFormatter

from apps.web.models import CodeAnnotation


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

        files, directories = self.get_files_directories(absolute_path, relative_path)

        context['files'] = files
        context['directories'] = directories
        context['relative_path'] = relative_path
        context['parent_directory'] = parent_directory
        return self.render_to_response(context)

    def get_files_directories(self, absolute_path, relative_path):
        directories = []
        files = []

        annotations = set(CodeAnnotation.objects.values_list('path', flat=True).distinct())

        everything = os.listdir(absolute_path)
        everything = (n for n in everything if not any(fnmatch(n, ignore) for ignore in settings.FILE_EXCLUDE_PATTERNS))

        for f in everything:
            path = os.path.join(absolute_path, f)
            rel_path = relative_path + f
            if os.path.isdir(path):
                has_annotations = any(annotation.startswith(rel_path) for annotation in annotations)
                directories.append({'directory': f, 'has_annotations': has_annotations})
            else:
                files.append({'file': f, 'has_annotations': rel_path in annotations})

        files = sorted(files, key=itemgetter('file'))
        directories = sorted(directories, key=itemgetter('directory'))
        return files, directories


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

        relative_path = '/' + absolute_path[len(code_directory):]

        annotations = {}
        for annotation in CodeAnnotation.objects.filter(path=relative_path):
            annotations[annotation.line_number] = {'user': annotation.user, 'annotation': annotation.annotation}

        with open(absolute_path) as f:
            code = f.read()

        code = highlight(code, PythonLexer(), Formatter(annotations=annotations, linenos='inline', linespans='line'))

        context['code'] = code
        context['css'] = HtmlFormatter().get_style_defs('.highlight')
        context['relative_path'] = relative_path
        return self.render_to_response(context)


class Formatter(HtmlFormatter):
    def __init__(self, annotations, *args, **kwargs):
        super(Formatter, self).__init__(*args, **kwargs)
        self.annotations = annotations

    def _wrap_linespans(self, inner):
        s = self.linespans
        i = self.linenostart - 1
        for t, line in inner:
            if t:
                i += 1
                if i in self.annotations:
                    annotation = self.annotations[i]
                    tooltip = '<span data-toggle="tooltip" data-placement="bottom" data-toggle="tooltip" ' + \
                              'title="{}: {}" class="annotation"><i class="fa fa-comment fa-fw"> </i> </span>'
                    tooltip = tooltip.format(annotation['user'].get_full_name(), annotation['annotation'])
                    yield 1, '<span id="%s-%d">%s%s</span>' % (s, i, tooltip, line)
                else:
                    yield 1, '<span id="%s-%d"><span class="fa fa-fw"></span> %s</span>' \
                          % (s, i, line)
            else:
                yield 0, line


class SubmitView(CreateView):
    model = CodeAnnotation
    fields = ('annotation', 'line_number', 'path')

    def form_valid(self, form):
        annotation = form.save(commit=False)
        annotation.user = self.request.user
        annotation.save()
        return redirect('{}?path={}#line-{}'.format(reverse('web:annotate'), annotation.path, annotation.line_number))

    def form_invalid(self, form):
        print(form.errors)
