from unittest import skip

from django.test import TestCase

from experiments.forms import ChangeSlugForm, EMPTY_SLUG_ERROR
from experiments.tests.tests_helper import create_experiment


class ChangeSlugFormTest(TestCase):

    def test_form_item_input_has_placeholder_and_css_classes(self):
        form = ChangeSlugForm()
        self.assertIn('placeholder="Type new slug"', form.as_p())
        self.assertIn('class="form-control input-lg"', form.as_p())

    def test_form_validation_for_blank_items(self):
        form = ChangeSlugForm(data={'slug': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['slug'], [EMPTY_SLUG_ERROR])

    @skip
    def test_form_validation_for_non_unique_slug(self):
        # TODO: resume chapter 15 of Obey The Testing Goat to test for
        # TODO: non unique slug
        create_experiment(1)
        other_experiment = create_experiment(1)

        form = ChangeSlugForm(data={'slug': other_experiment.slug})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['slug'], 'Message to display')
