from django.db.models.sql.compiler import SQLCompiler, SQLInsertCompiler
from django.db.models.sql.datastructures import EmptyResultSet
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, SINGLE, MULTI
from django.db.models.sql.compiler import order_modified_iter
from threading import local
from SQLRewrite import rewrite_query

_thread_request_id = local()


def get_session(params):
    rid = ''
    if hasattr(_thread_request_id, 'rid'):
        rid = _thread_request_id.rid
    
    if rid is None:
        if len(params) != 0:
            rid = params[0]
        else:
            rid = ''

    return rid 

def add_session_ins(self, return_id=False):
        assert not (return_id and len(self.query.objs) != 1)
        self.return_id = return_id
        cursor = self.connection.cursor()
        for sql, params in self.as_sql():
            sql = sql+" /* "+ get_session(params) +" */"
            cursor.execute(sql, params)
        if not (return_id and cursor):
            return
        if self.connection.features.can_return_id_from_insert:
            return self.connection.ops.fetch_returned_insert_id(cursor)
        return self.connection.ops.last_insert_id(cursor,
                self.query.get_meta().db_table, self.query.get_meta().pk.column)

def add_session(self, result_type=MULTI):

        try:
            sql, params = self.as_sql()
            if not sql:
                raise EmptyResultSet
        except EmptyResultSet:
            if result_type == MULTI:
                return iter([])
            else:
                return
        
        sql,params = rewrite_query(sql,params,get_session(params))

        sql = sql+" /* "+ get_session(params) +" */"

        cursor = self.connection.cursor()
        cursor.execute(sql, params)

        if not result_type:
            return cursor
        if result_type == SINGLE:
            if self.ordering_aliases:
                return cursor.fetchone()[:-len(self.ordering_aliases)]
            return cursor.fetchone()

        # The MULTI case.
        if self.ordering_aliases:
            result = order_modified_iter(cursor, len(self.ordering_aliases),
                    self.connection.features.empty_fetchmany_value)
        else:
            result = iter((lambda: cursor.fetchmany(GET_ITERATOR_CHUNK_SIZE)),
                    self.connection.features.empty_fetchmany_value)
        if not self.connection.features.can_use_chunked_reads:
            return list(result)
        return result


def patch(request):
    try:
        lrid = request.user.username
        _thread_request_id.rid = lrid 
    except KeyError:
        _thread_request_id.rid = ''
     
        
    if not hasattr(SQLCompiler, '_execute_sql'):
        SQLCompiler._execute_sql = SQLCompiler.execute_sql
        SQLCompiler.execute_sql = add_session
        SQLInsertCompiler._execute_sql = SQLInsertCompiler.execute_sql
        SQLInsertCompiler.execute_sql = add_session_ins