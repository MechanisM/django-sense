import time

from django.conf import settings

from django.template.loader import get_template
from django.template import Template, Context

from django.test.signals import template_rendered
from django.test.utils import instrumented_test_render
import pprint

# Monkey-patch the template objects in order to keep track of the
# templates used and their origins
if Template.render != instrumented_test_render:
    Template.original_render = Template.render
    Template.render = instrumented_test_render

old_template_init = Template.__init__
old_template_render = Template.render

# Patches
def init_patch(self, template_string, origin=None, name='<Unknown Template>'):
    self.origin = origin
    old_template_init(self, template_string, origin, name)

def render_patch(self, ctx):
    self.context = ctx.dicts
    return old_template_render(self, ctx)

# Apply patches
Template.__init__ = init_patch
Template.render = render_patch

class TemplateMiddleware:

    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('template'):
            self.time_started = time.time()
            self.templates_used = []
            self.contexts_used = []

            template_rendered.connect(
                self._storeRenderedTemplates
            )

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('template'):
            display = get_template('templates.html')

            pp = pprint.PrettyPrinter()

            templates = [
                (
                    t.name,
                    t.origin and t.origin.name or 'No origin',
                    pp.pformat(t.context)
                )
                for t in self.templates_used
            ]

            a = [t.context for t in self.templates_used]
            pp.pprint(a[0])

            template_context = Context({
                'server_time': time.time() - self.time_started,
                'templates': templates,
                'template_dirs': settings.TEMPLATE_DIRS,
            })

            response.content = display.render(template_context)

        return response

    def _storeRenderedTemplates(self, signal, sender, template, context, **kwargs):
        self.templates_used.append(template)
        self.contexts_used.append(context)
