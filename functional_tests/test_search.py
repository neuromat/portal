from selenium.webdriver.common.keys import Keys
from experiments.models import Experiment
from functional_tests.base import FunctionalTest

import time


class SearchTest(FunctionalTest):

    def test_simple_word_returns_experiments(self):

        # A researcher is delighted with the NED Portal. She decides to
        # search for experiments that contains "Braquial Plexus" in whatever
        # part of the portal. The search engine is complex. Some of its
        # facilits consists in ignoring upper/lower case letters, search for
        # terms individually and in whatever order too.
        search_form = self.browser.find_element_by_id('search_form')
        search_box = self.browser.find_element_by_id(
            'search_box')
        search_box.send_keys('Braquial Plexus')
        self.browser.find_element_by_id('submit_keys').click()
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)
        # The search engine searches in all the site content.
        # As there are "Braquial Plexus", "braquial plexus", "Braquial",
        # "braquial", "Plexus", and "plexus" in experiments data per se,
        # studies, groups, and study keywords, she sees in Search results
        # one list for each of them.
        search_table_title = self.browser.find_element_by_tag_name('h2').text
        self.assertEqual(search_table_title, 'Search Results')
        experiment_searched = Experiment.objects.get(title="Plexus")
        self.assertIn(experiment_searched.title, 'Braquial Plexus')

        # As she clicks in all of the itens of that lists, she is redirected
        # the corresponding experiment detail view directly at the point
        # whose search found the terms. These terms are hilighted.


