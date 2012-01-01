import sys
import os
import re
from collections import defaultdict

import cProfile
import pstats
import simplejson

from cStringIO import StringIO

from django.conf import settings

from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse

words_re = re.compile( r'\s+' )

group_prefix_re = [
    re.compile( "^.*/django/[^/]+" ),
    re.compile( "^(.*)/[^/]+$" ), # extract module path
    re.compile( ".*" ),           # catch strange entries
]

site_package_re = re.compile("^.*/site-packages/(?P<module>[a-zA-Z_]\w*)?")
stdlib_re = re.compile("^.*/lib/python.*/(?P<module>[a-zA-Z_]\w*)?")
core_re = re.compile(".*(\{.*\})")

class ProfileMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def get_group(self, file):
        for g in group_prefix_re:
            name = g.findall( file )
            if name:
                return name[0]

    def get_summary(self, results_dict, sum):
        lst = [ (item[1], item[0]) for item in results_dict.items() ]
        lst.sort( reverse = True )
        lst = lst[:40]

        dct = {}
        for item in lst:
            dct[item[1]] = 100*item[0]/sum if sum else 0

        return dct

    def summary_for_files(self, stats_str):
        stats_str = stats_str.split("\n")[5:]

        mystats = {}
        mygroups = {}
        mymodules = {}
        myclasses = {
            'business' : 0,
            'stdlib'   : 0,
            'cpython'  : 0,
            'django'   : 0,
            'sql'      : 0,
            'diskio'   : 0
        }

        mybusiness = defaultdict(int)
        mystdlib = defaultdict(int)
        mycpython = defaultdict(int)
        mydjango = defaultdict(int)
        mysql = defaultdict(int)
        mydiskio = defaultdict(int)

        sum = 0

        for s in stats_str:
            fields = words_re.split(s);
            corecall = core_re.match(s)

            # Example:
            # 3    0.004    0.001    0.004    0.001
            # {method # 'execute' of 'psycop g2._psycopg.cursor' objects}
            if corecall:
                callname = corecall.groups(0)[0]

                time = float(fields[2])
                mycpython[callname] += time

                if """of 'file' objects""" in callname:
                    myclasses['diskio'] += time
                    mydiskio[callname] += time

                # TODO: support for mysql and sqlite
                elif """of 'psycopg2._psycopg.cursor'""" in callname:
                    myclasses['sql'] += time
                    mysql[callname] += time
                else:
                    myclasses['cpython'] += time

            # Example:
            # 166    0.001    0.000    0.002    0.000 # /home/.virtualenvs/s/li
            # /python2.7/site-packages/django/utils/functional.py:254(wrapper)
            elif len(fields) == 7:

                try:
                    time = float(fields[2])
                except:
                    # A header line
                    continue

                sum += time

                try:
                    filename, lineno = fields[6].split(":")
                except ValueError:
                    filename = fields[6]

                # Files
                if not filename in mystats:
                    mystats[filename] = 0
                mystats[filename] += time


                if 'django' in filename:
                    mydjango[filename] += time

                # Groups
                group = self.get_group(filename)
                if not group in mygroups:
                    mygroups[ group ] = 0
                mygroups[ group ] += time

                # Modules
                site_package = site_package_re.match(filename)
                stdlib_package = stdlib_re.match(filename)
                core_call = core_re.match(filename)

                # a site-package
                if site_package:
                    module = site_package.groupdict().get('module', None)

                    # Some core Django module
                    if module == 'django':
                        myclasses['django'] += time

                # standard library
                elif stdlib_package:
                    module = stdlib_package.groupdict().get('module', None)
                    myclasses['stdlib'] += time
                    mystdlib[module] += time

                # business logic
                else:
                    module = filename
                    myclasses['business'] += time
                    mybusiness[module] += time


                if not module in mymodules:
                    mymodules[ module ] = 0

                mymodules[ module ] += time

        profiles = {
            'byfile'    : self.get_summary(mystats, sum),
            'bygroup'   : self.get_summary(mygroups, sum),
            'bypackage' : self.get_summary(mymodules, sum),
            'byclass'   : self.get_summary(myclasses, sum),

            'business'  : self.get_summary(mybusiness , sum),
            'stdlib'    : self.get_summary(mystdlib , sum),
            'cython'    : self.get_summary(mycpython, sum),
            'django'    : self.get_summary(mydjango, sum),
            'sql'       : self.get_summary(mysql, sum),
            'diskio'    : self.get_summary(mydiskio, sum),
        }

        return profiles

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('prof'):

            self.profiler.create_stats()
            out = StringIO()
            stats = pstats.Stats(self.profiler, stream=out)

            stats.sort_stats('time').print_stats(.2)
            response.content = out.getvalue()

            stats_str = out.getvalue()

            # The profiler dump
            raw_dump = "\n".join(stats_str.split("\n")[:40])

            # Our profiler dump
            profiles =  self.summary_for_files(stats_str)

            t = get_template('profile.html')
            html = t.render(Context({
                'raw_dump': raw_dump,
                'raw_json': simplejson.dumps(profiles, indent=4),
                'profiles': profiles,
            }))
            return HttpResponse(html)
        else:
            return response
