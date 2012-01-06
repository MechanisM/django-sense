import time

from django.conf import settings
from django.db import connection
from django.db.backends.util import CursorDebugWrapper

from django.template.loader import get_template
from django.template import Context

# Monkey-patch the execute method to include a stack trace
def my_execute(self, sql, params=()):
    start = time.time()

    try:
        return self.cursor.execute(sql, params)
    finally:
        stop = time.time()
        executed_sql = self.db.ops.last_executed_query(
            self.cursor, sql, params
        )
        self.db.queries.append({
            'sql': executed_sql,
            'time': "%.3f" % (stop - start),
            'bad': (stop - start) > 0.01,
            'params': params,
            'sql_no_params': sql,
        })

CursorDebugWrapper.execute = my_execute

class QueryMiddleware:
    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('query'):
            self.time_started = time.time()
            self.sql_offset_start = len(connection.queries)

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and request.REQUEST.has_key('query'):
            sql_queries = connection.queries[self.sql_offset_start:]

            # Pretty Print the SQL
            sql_total = 0.0
            for query in sql_queries:
                query['sql'] = pprint_sql(query['sql'])
                sql_total += float(query['time'])

            # Count the most-executed queries
            most_executed = {}
            for query in sql_queries:
                reformatted = pprint_sql(query['sql_no_params'])
                most_executed.setdefault(reformatted, []).append(query)

            most_executed = most_executed.items()
            most_executed.sort(key = lambda v: len(v[1]), reverse=True)
            most_executed = most_executed[:10]

            template_context = Context({
                'sql': sql_queries,
                'sql_total': sql_total,
                'bad_sql_count': len([s for s in sql_queries if s['bad']]),
                'most_executed': most_executed,
                'server_time': time.time() - self.time_started,
            })

            response.content = get_template('django_sense/queries.html').render(template_context)

        return response

def pprint_sql(sql):
    sql = sql.replace('`,`', '`, `')
    sql = sql.replace(' FROM ', ' \n    FROM ')
    sql = sql.replace(' WHERE ', ' \n    WHERE ')
    sql = sql.replace(' ORDER BY ', ' \n    ORDER BY ')
    sql = sql.replace(' ON ', ' \n    ON ')
    sql = sql.replace(' AND ', ' \n    AND ')
    sql = sql.replace(' LIMIT ', ' \n    LIMIT ')
    sql = sql.replace(' INNER JOIN ', ' \n    INNER JOIN ')
    sql = sql.replace(' LEFT OUTER JOIN ', ' \n    LEFT OUTER JOIN ')
    return sql
