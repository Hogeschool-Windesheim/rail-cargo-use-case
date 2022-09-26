"""
This module contains various regular expressions for
common kinds of strings.

These expressions are mainly referenced in api.urls.py,
which has to check that path arguments have the proper format.
They can also be used in serializer.py, which checks input data.

The patterns are defined as flat strings rather than compiled
Pattern objects so that they can be placed in-line where they are called.
"""

username = '[a-z0-9A-Z_\-:]+'
setting = '[a-z0-9A-Z_\-:]+'
assetID = '[a-z0-9]{64}'
slpID = '[a-zA-Z0-9\-_:\.]+'
