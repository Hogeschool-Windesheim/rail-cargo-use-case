"""
A list of order status encodings, and associated collections and helper functions.

These follow Wout Hofman's specification, except for "UNKNOWN", which is a placeholder for development purposes, and "REJECTED", which was added by the development team.
"""

from .status import Status

class OrderStatus(Status):
    """
    Statuses for the Order object
    """
    TO_BE_CONFIRMED = 0
    CONFIRMED = 1
    STARTED = 2
    COMPLETED = 3
    REJECTED = 4
    statuses = [
        TO_BE_CONFIRMED, CONFIRMED, STARTED, COMPLETED, REJECTED
    ]
