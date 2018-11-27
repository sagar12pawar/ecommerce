import mock
from oscar.core.loading import get_model
from oscar.test import factories

from ecommerce.extensions.offer.applicator import CustomApplicator
from ecommerce.extensions.test.factories import ConditionalOfferFactory, ProgramOfferFactory
from ecommerce.tests.testcases import TestCase

BasketAttribute = get_model('basket', 'BasketAttribute')
BasketAttributeType = get_model('basket', 'BasketAttributeType')
BUNDLE = 'bundle_identifier'
LOGGER_NAME = 'ecommerce.extensions.offer.applicator'


class CustomApplicatorTests(TestCase):
    """ Tests for the Program Applicator. """

    def setUp(self):
        self.applicator = CustomApplicator()
        self.basket = factories.create_basket(empty=True)
        self.user = factories.UserFactory()

    def create_bundle_attribute(self, bundle_id):
        """ Helper to add a bundle attribute to a basket. """
        BasketAttribute.objects.create(
            basket=self.basket,
            attribute_type=BasketAttributeType.objects.get(name=BUNDLE),
            value_text=bundle_id,
        )

    def assert_correct_offers(self, expected_offers):
        """ Helper to verify applicator returns the expected offers. """
        # No need to pass a request to get_offers since we currently don't support session offers
        offers = self.applicator.get_offers(self.basket, self.user)
        self.assertEqual(offers, expected_offers)

    def test_get_offers_with_bundle(self):
        """ Verify that only offers related to the bundle id are returned. """
        program_offers = [ProgramOfferFactory()]
        bundle_id = program_offers[0].condition.program_uuid
        self.create_bundle_attribute(bundle_id)

        ConditionalOfferFactory.create_batch(2)  # Unrelated offers that should not be returned

        self.applicator.get_site_offers = mock.Mock()
        self.assert_correct_offers(program_offers)
        self.assertFalse(self.applicator.get_site_offers.called)  # Verify there was no attempt to get all site offers

    def test_get_offers_without_bundle(self):
        """ Verify that all non bundle offers are returned if no bundle id is given. """
        program_offers = [ProgramOfferFactory()]
        site_offers = ConditionalOfferFactory.create_batch(3)

        self.applicator.get_program_offers = mock.Mock()

        self.assert_correct_offers(program_offers + site_offers)

        self.assertFalse(self.applicator.get_program_offers.called)  # Verify there was no attempt to match off a bundle
