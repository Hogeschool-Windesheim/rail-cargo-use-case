from rest_framework.authtoken.models import Token
from rest_framework import status as http_status

from django.urls import reverse
from django.contrib.auth.models import User

from api.status.order_status import OrderStatus

from api.tests.SLPTestCase import SLPTestCase

class OrderFlowTest(SLPTestCase):
    '''
    Test order creation, confirmation, or rejection.
    
    This class does NOT test Order data object formatting,
    i.e. it does not test whether faulty order data objects are correctly rejected.
    '''

    # Test body here
    def testOrderGet(self):
        """
        Test order retrieval

        @order_count determines
        how many orders are posted and retrieved.
        """
        
        order_count = 2 # TODO could this be a function arg?
        order_ids = []

        for order_index in range(order_count):
            # Post order
            order_ids.append(self.postOrder())


        # Set up user variables
        alice = User.objects.get(username='alice')
        alice_token = Token.objects.get(user=alice).key
        
        # Authenticate as Alice
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + alice_token)

        # Get orders
        url = reverse('order')
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # Check orders are contained in the response data
        for order_id in order_ids:
            self.assertIn(order_id, response.data)
        print('Successfully retrieved {} orders'.format(order_count))

        # Check orders have correct status
        # All orders were newly created so they should
        # have TO BE CONFIRMED status.
        for order_id in order_ids:
            self.assertEqual(response.data[order_id]['metadata']['status'], OrderStatus.TO_BE_CONFIRMED)
        print('Order statuses have the expected value')

    def testOrderConfirm(self):
        '''
        Test order creation and confirmation
        '''
        # Set up user variables
        alice = User.objects.get(username='alice')
        alice_token = Token.objects.get(user=alice).key
        bob = User.objects.get(username='bob')
        bob_token = Token.objects.get(user=bob).key

        # Post an order
        order_asset_id = self.postOrder()
        print('Order-to-be-confirmed successfully posted at ID:', order_asset_id)

        #############################
        # Order creation completed,
        # Confirmation starts here
        #############################

        # Prepare the url: PUT call to the orders endpoint, including asset ID
        url = reverse('order_detail', kwargs={'asset_id':order_asset_id})
        
        # As Alice
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + alice_token)

        # Let Alice try confirming her own order
        response = self.client.put(url)
        self.assertNotEqual(response.status_code, http_status.HTTP_200_OK)
        print('Correctly blocked Alice from confirming her own order')

        # Authenticate as Bob
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + bob_token)
        
        # Let Bob confirm order; expect HTTP200
        response = self.client.put(url)
        if response.status_code != http_status.HTTP_200_OK:
            print('Error while confirming order:', response.data)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        print('Successfully confirmed order as Bob')
        # Check that the order status has properly mutated
        self.assertEqual(OrderStatus.get_status(order_asset_id), OrderStatus.CONFIRMED)

    def testOrderReject(self):
        '''
        Test order creation and rejection
        '''
        # Set up user variables
        alice = User.objects.get(username='alice')
        alice_token = Token.objects.get(user=alice).key
        bob = User.objects.get(username='bob')
        bob_token = Token.objects.get(user=bob).key
        
        order_asset_id = self.postOrder()
        print('Order-to-be-rejected successfully posted at ID:', order_asset_id)

        #############################
        # Order creation completed,
        # Rejection starts here
        #############################

        # Prepare the url
        url = reverse('order_detail', kwargs={'asset_id':order_asset_id})        
        
        # As Alice
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + alice_token)

        # Let Alice try rejecting her own order
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, http_status.HTTP_200_OK)
        print('Correctly blocked Alice from rejecting her own order')

        # Authenticate as Bob
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + bob_token)
        
        # Let Bob reject order; expect HTTP200
        response = self.client.delete(url)
        if response.status_code != http_status.HTTP_200_OK:
            print('Error while rejecting order:', response.data)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        print('Successfully rejected order as Bob')
        # Check that the order status has properly mutated
        self.assertEqual(OrderStatus.get_status(order_asset_id), OrderStatus.REJECTED)

class OrderFormattingTest(SLPTestCase):
    '''
    Test whether faulty Order data objects are correctly rejected.
    '''
    pass