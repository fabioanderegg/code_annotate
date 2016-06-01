import os
from fnmatch import fnmatch
from operator import itemgetter

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView, CreateView

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound

from apps.web.models import CodeAnnotation


class BaseView(TemplateView):
    def get_breadcrumbs(self, path):
        breadcrumbs = [{'path': '/', 'name': 'Root'}]
        if path != '':
            current_path = ''
            for split in path[1:].split('/'):
                current_path += '/' + split
                breadcrumbs.append({'path': current_path, 'name': split})
        return breadcrumbs


class BrowseView(BaseView):
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
        breadcrumbs = self.get_breadcrumbs(relative_path[:-1])

        parent_directory = os.path.realpath(os.path.join(absolute_path, os.path.pardir)) + os.path.sep
        parent_directory = '/' + parent_directory[len(code_directory):]

        files, directories = self.get_files_directories(absolute_path, relative_path)

        context.update({
            'files': files,
            'directories': directories,
            'relative_path': relative_path,
            'parent_directory': parent_directory,
            'breadcrumbs': breadcrumbs,
        })
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


class AnnotateView(BaseView):
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

        relative_path = '/' + absolute_path[len(code_directory):]
        breadcrumbs = self.get_breadcrumbs(relative_path)

        annotations = {}
        for annotation in CodeAnnotation.objects.filter(path=relative_path):
            annotations[annotation.line_number] = {'user': annotation.user, 'annotation': annotation.annotation}

        with open(absolute_path) as f:
            code = f.read()

        try:
            lexer = get_lexer_for_filename(absolute_path)
        except ClassNotFound:
            lexer = TextLexer()
        code = highlight(code, lexer, Formatter(annotations=annotations, linenos='inline', linespans='line'))

        context.update({
            'code': code,
            'css': HtmlFormatter().get_style_defs('.highlight'),
            'relative_path': relative_path,
            'breadcrumbs': breadcrumbs,
        })
        return self.render_to_response(context)


class Formatter(HtmlFormatter):
    def __init__(self, annotations, **options):
        super(Formatter, self).__init__(**options)
        self.annotations = annotations

    def _wrap_linespans(self, inner):
        s = self.linespans
        i = self.linenostart - 1
        for t, line in inner:
            if t:
                i += 1
                if i in self.annotations:
                    annotation = self.annotations[i]
                    tooltip = '<span data-toggle="tooltip" data-placement="left" data-toggle="tooltip" ' + \
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
