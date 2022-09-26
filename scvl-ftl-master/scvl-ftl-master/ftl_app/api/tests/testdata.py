"""
A module collecting various pieces of test data.
"""

from api.status.event_milestones import EventMilestones

orders = {
    'valid': [
        {
            'cargo':{
                'cargo_type':'General',
                'package_type': 'Pallets',
                'package_count': 6
            },
            'time_of_acceptance':'2019-10-18 16:19:25',
            'place_of_acceptance':'Soesterberg',
            'time_of_delivery':'2019-10-19 08:00:01',
            'place_of_delivery':'Den Haag',
            'reference_id': 'ABCD1234/5-6'
        }
    ],
    'invalid':[

    ]
}


events = {
    'valid': [
        {
            'order_asset_id':None,
            'event':{
                'time':'2019-10-19 08:00:01',
                'place':'Den Haag',
                'milestone': EventMilestones.DISCHARGE
            }
        }
    ],
    'invalid':[]
}

# Sequences of events posted to an order.
event_sequences = {
    'valid': [
        {
            'order':orders['valid'][0],
            'events': [
                {
                    'event':{
                        'time':'2019-10-18 16:19:26',
                        'place':'Soesterberg',
                        'milestone': EventMilestones.LOAD
                    }
                },
                {
                    'event':{
                        'time':'2019-10-18 16:19:27',
                        'place':'Soesterberg',
                        'milestone': EventMilestones.DEPART
                    }
                },
                {
                    'event':{
                        'time':'2019-10-18 16:19:28',
                        'place':'Gouda',
                        'milestone': EventMilestones.POSITION
                    }
                },
                {
                    'event':{
                        'time':'2019-10-18 16:19:29',
                        'place':'Den Haag',
                        'milestone': EventMilestones.ARRIVE
                    }
                },
                {
                    'event':{
                        'time':'2019-10-18 16:19:30',
                        'place':'Den Haag',
                        'milestone': EventMilestones.DISCHARGE
                    }
                },
            ]
        }
    ],
    'invalid':[

    ]
}