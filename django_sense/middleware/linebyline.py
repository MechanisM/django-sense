import os

import inspect
import linecache
import simplejson

from line_profiler import LineProfiler

from django.conf import settings

from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse

def do_stats(stats):
    """
    Show the gathered statistics.
    """
    return show_text(stats.timings, stats.unit)

def show_func(filename, start_lineno, func_name, timings, unit):
    """
    Show results for a single function.
    """
    print "File: %s" % filename
    print "Function: %s at line %s" % (func_name, start_lineno)

    d = {}
    total_time = 0.0
    linenos = []

    for lineno, nhits, time in timings:
        total_time += time
        linenos.append(lineno)

    #print "Total time: %g s" % (total_time * unit)

    if not os.path.exists(filename):
        raise Exception("Could not find file %s" % filename)
        # Fake empty lines so we can see the timings, if not the code.
        nlines = max(linenos) - min(min(linenos), start_lineno) + 1
        sublines = [''] * nlines
    else:
        all_lines = linecache.getlines(filename)
        sublines = inspect.getblock(all_lines[start_lineno-1:])

    for lineno, nhits, time in timings:
        d[lineno] = (
            nhits,
            '%2.3f s' % (time * unit),
            '%5.1f' % (float(time) / nhits),
            '%5.1f' % (100*time / total_time)
        )

    linenos = range(start_lineno, start_lineno + len(sublines))

    empty = ('', '', '', '')

    # ('Line #', 'Hits', 'Time', 'Per Hit', '% Time', 'Line Contents')

    results = []

    for lineno, line in zip(linenos, sublines):
        nhits, time, per_hit, percent = d.get(lineno, empty)
        results.append((lineno, nhits, time, per_hit, percent,
            line.rstrip('\n').rstrip('\r')))
    return results

def show_text(stats, unit):
    """
    Show text for the given timings.
    """
    results = []
    for (fn, lineno, name), timings in sorted(stats.items()):
        results.append(show_func(fn, lineno, name, stats[fn, lineno, name], \
            unit))
    return results

class LineByLine(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('line'):
            request.devserver_profiler = LineProfiler()
            request.devserver_profiler_run = True

            request.devserver_profiler.enable_by_count()
            _unwrap_closure_and_profile(request.devserver_profiler, view_func)

    def process_complete(self, request):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('line'):
            request.devserver_profiler.disable_by_count()

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('line'):
            pstats = request.devserver_profiler.get_stats()
            stats = show_text(pstats.timings, pstats.unit)

            t = get_template('django_sense/codemap.html')
            html = t.render(Context({
                'json': simplejson.dumps(stats)
            }))
            return HttpResponse(html)
        else:
            return response

def _unwrap_closure_and_profile(profiler, func):
    if not hasattr(func, 'func_code'):
        return

    # Don't profile decorators
    if func.func_code.co_name != '_wrapped_view' and func.func_name != '<lambda>':
        profiler.add_function(func)

    # Decorators store their wrapped functions in the
    # func_closure, and only decorators have this non-null
    if func.func_closure:
        for cell in func.func_closure:
            if hasattr(cell.cell_contents, 'func_code'):
                # not a decorator
                if cell.cell_contents.func_name != 'lambda':
                    _unwrap_closure_and_profile(profiler, cell.cell_contents)
