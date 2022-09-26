from rest_framework.authtoken.models import Token
from rest_framework import status as http_status

from django.urls import reverse
from django.contrib.auth.models import User

from api.status.order_status import OrderStatus
from api.status.event_milestones import EventMilestones
from api.tests.SLPTestCase import SLPTestCase
import api.tests.testdata as testdata

import json

class EventTestCase(SLPTestCase):
    """
    For events, further functionality is needed on top of the
    general SLP test case that was used e.g. for order testing.
    """
    @classmethod
    def postEvent(cls, event_data, order_asset_id, username_a='alice', username_b='bob'):
        """
        Post an event according to the event data.
        (Analogous to SLPTestCase.postOrder())
        Returns the asset ID of the posted event.
        Raises an error if something went wrong in the process.
        """
        # Set up user variables
        # TODO this could probably happen in the class init
        alice = User.objects.get(username=username_a)
        alice_token = Token.objects.get(user=alice).key
        bob = User.objects.get(username=username_b)
        bob_token = Token.objects.get(user=bob).key

        # Authenticate as Bob
        # (Bob typically has the service provider role)
        cls.client.credentials(HTTP_AUTHORIZATION='Token ' + bob_token)

        # Post an event
        url = reverse('event')
        postdata = {
            'event': event_data,
            'order_asset_id': order_asset_id
        }
        print("Posting event with following data: \n{}".format(json.dumps(postdata)))
        response = cls.client.post(url, data=postdata, format='json')

        # Check that the request was properly processed
        if response.status_code != http_status.HTTP_200_OK:
            print('Error while posting event:', str(response.data))
            raise Exception

        # Extract and return the event asset ID
        event_asset_id = response.data
        return event_asset_id

class EventTest(EventTestCase):
    '''
    Test event creation and retrieval,
    and test appropriate updating of order status based on event creation.
    '''
    
    def testEventPost(self):
        """
        Test event posting.
        """

        order_asset_id = self.postOrder()
        self.confirmOrder(order_asset_id)

        event = testdata.events['valid'][0]
        event.update({'order_asset_id':order_asset_id})

        url = reverse('event')
        response = self.client.post(url, data=event, format='json')
        if response.status_code != http_status.HTTP_200_OK:
            print("Error while posting <{}>: {}".format(response.status_code, response.data))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        print('Successfully posted event')

    def testEventSequences(self):
        """
        Test the posting of sequences of events.
        """
        # First, loop over all valid testcases
        for sequence in testdata.event_sequences['valid']:
            # Post the order, which is stored separately from the event sequence
            order_data = sequence['order']
            order_asset_id = self.postOrder(order_data=order_data)
            print("Posted order as asset {} for FTL from {} to {}".format(
                    order_asset_id, order_data['place_of_acceptance'],
                    order_data['place_of_delivery'])
            )
            # Confirm the order
            self.confirmOrder(order_asset_id)

            # Now go through the sequence of events
            for event_call in sequence['events']:
                # Post the event
                event_data = event_call['event']
                event_asset_id = self.postEvent(event_data=event_data, order_asset_id=order_asset_id)
                print("Posted an event with milestone {}, identified as asset {}".format(
                        event_data['milestone'], event_asset_id)
                )
                # TODO maybe test GET function here somehow?
                # Check whether the event triggered the correct status transition
                (_, target_status) = EventMilestones.transitions[event_data['milestone']]
                actual_status = OrderStatus.get_status(order_asset_id)
                self.assertEqual(actual_status, target_status)
                print("Order asset status is now {}, as desired".format(actual_status))

    def testEventGet(self):
        """
        Test event retrieval
        @eventCount: the number of events sent
        """
        eventCount = 2

        # First set up an order with some events
        sequence = testdata.event_sequences['valid'][0]
        # Post the order, which is stored separately from the event sequence
        order_data = sequence['order']
        order_asset_id = self.postOrder(order_data=order_data)
        print("Posted order as asset {} for FTL from {} to {}".format(
                order_asset_id, order_data['place_of_acceptance'],
                order_data['place_of_delivery'])
        )
        # Confirm the order too, so it has the proper status
        self.confirmOrder(order_asset_id)
        # Post a couple of events
        for eventCall in sequence['events'][:eventCount]:
            eventData = eventCall['event']
            event_asset_id = self.postEvent(event_data=eventData, order_asset_id=order_asset_id)
            print("Posted an event with milestone {}, identified as asset {}".format(
                    eventData['milestone'], event_asset_id))
        
        # Post the GET call
        url = reverse('order_detail', kwargs={'asset_id':order_asset_id})
        # Check both users' perspectives..
        for username in ("alice", "bob"):
            # Authenticate as user
            user_token = Token.objects.get(user__username=username)
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_token.key)
            # Do the GET call
            response = self.client.get(url)
            print("Retrieving order as {} yielded: {}".format(username, response.data))
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            # Assert the order is there
            self.assertIn('order', response.data.keys())
            # Check that the correct number of events were found
            self.assertEqual(len(response.data['events']), eventCount)
            # Check that order status is correct
            self.assertEqual(response.data['metadata']['status'], OrderStatus.STARTED)
