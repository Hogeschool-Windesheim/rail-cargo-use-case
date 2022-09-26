"""
A list of event milestones, and associated collections and helper functions.

These follow Wout Hofman's specification, except for "UNKNOWN", which is a placeholder for development purposes.
"""

from .order_status import OrderStatus
from .status import Status

class EventMilestones(Status):
    """
    Milestone codes for Event objects
    """
    ARRIVE = 101
    DEPART = 106
    LOAD = 110
    DISCHARGE = 112
    POSITION = 114
    # List of statuses
    statuses = [
    ARRIVE, DEPART, LOAD, DISCHARGE, POSITION
    ]
    # List of OrderStatus transitions triggered by milestones
    transitions = {
        LOAD: (OrderStatus.CONFIRMED, OrderStatus.STARTED),
        DEPART: (OrderStatus.STARTED, OrderStatus.STARTED), # No transition
        POSITION: (OrderStatus.STARTED, OrderStatus.STARTED), # No transition
        ARRIVE: (OrderStatus.STARTED, OrderStatus.STARTED), # No transition
        DISCHARGE: (OrderStatus.STARTED, OrderStatus.COMPLETED),
    }