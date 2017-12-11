django_SQLrewrite
=================

## Required modules:
* sqlparse

## Configuration:
1. Add middleware to the last postition to the **MIDDLEWARE_CLASSES** list in settings.py.
2. Add the following list to settings.py:
```python
SQL_REWRITE_REGEXP=(
                    ('TABLE_NAME.COLUMN_NAME','REGEXP'),
                    )
```
**REGEXP** will be used in SQL statement (for example "SELECT * FROM test WHERE REGEXP 'test2'").

The **%s** (can be used in the **REGEXP**) will be replaced by username (django access control mechanism).
