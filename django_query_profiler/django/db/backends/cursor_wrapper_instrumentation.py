"""
This module contains the part where we wrap CursorWrapper and CursorDebugWrapper with our function
that calls to "do something/nothing" after the query is executed
"""

from time import time
from typing import Any, Callable, Union

from django.db.backends.utils import CursorDebugWrapper, CursorWrapper

from django_query_profiler.query_signature.data_storage import \
    query_profiler_thread_local_storage


class QueryProfilerCursorWrapper(CursorWrapper):
    def __init__(self, cursor, db: str, db_row_count: Union[int, None]):
        super().__init__(cursor, db)
        self.db_row_count = db_row_count

    def execute(self, sql, params=None):
        return _helper(self, base_class_func=super().execute, sql=sql, params=params)

    def executemany(self, sql, param_list):
        return _helper(self, base_class_func=super().executemany, sql=sql, params=param_list)


class QueryProfilerCursorDebugWrapper(QueryProfilerCursorWrapper, CursorDebugWrapper):
    """
    The code for this is exactly the same as QueryProfilerCursorWrapper, except the base class would be
    CursorDebugWrapper.  Seems like a perfect use case of multiple inheritance
    See https://rhettinger.wordpress.com/2011/05/26/super-considered-super/ if this looks confusing
    """
    pass


def _helper(query_profiler_cursor_wrapper: CursorWrapper, base_class_func: Callable, sql: str, params: Any):
    """
    This function calls invokes the "do something/nothing" with all the parameters
    """
    start_time = time()
    try:
        output = base_class_func(sql, params)
    finally:
        end_time = time()
        query_execution_time_in_micros = int((end_time - start_time) * 1000 * 1000)

        query_profiler_thread_local_storage.add_query_profiler_data(
            query_without_params=sql,
            params=params,
            target_db=query_profiler_cursor_wrapper.db.alias,
            query_execution_time_in_micros=query_execution_time_in_micros,
            db_row_count=query_profiler_cursor_wrapper.db_row_count)
    return output
