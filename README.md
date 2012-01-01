django-sense is a friendly fork of [django-clue](https://github.com/garethr/django-clue/).

The main features are:

* Line-by-line profiling of views, with a heatmap view in the
  browser.
* Graphical frontend to cProfile snapshots. 

Credits:
--------

* `line-profiler` - The C backend for line-by-line profiling.
* `django-clue` - Template & Query profilers.
* `django-devserver` - Inspired the line by line profiler.

URL Patterns
------------

PROFILE SNAPSHOT - `localhost:8000/foo/bar/?prof`
LINE BY LINE PROFILE - `localhost:8000/foo/bar/?line`
TEMPLATE USAGE - `localhost:8000/foo/bar/?template`
QUERY USAGE - `localhost:8000/foo/bar/?query`

Usage
-----

    INSTALLED_APPS = (
        ...
       'django-sense',
       ...
    )

    MIDDLEWARE_CLASSES = (
        'django-sense.middleware.query.QueryMiddleware',
        'django-sense.middleware.profiler.ProfileMiddleware',
        'django-sense.middleware.template.TemplateMiddleware',
        'django-sense.middleware.linebyline.LineByLine',
    )

Caveats
------------

Line by line profiling tries its best to figure out which view
function you want to profile, but it can fail in some convoluted
call stacks. 

The profile snapshots are also done by cProfile which means that
multithreaded code ( gevent, psyco, eventlet ) may not be profile
properly single cProfile is not threadsafe.

License:
--------

Copyright (c) 2012 <stephen.m.diehl@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
