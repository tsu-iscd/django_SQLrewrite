"""
SQL Rewrite middleware
"""

import UserSessionSQLQuery

class UserSessionSQLQueryMiddleware:
    def process_request(self, request):
        UserSessionSQLQuery.patch(request)