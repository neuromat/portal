from django.core.management import call_command
from selenium.webdriver.common.keys import Keys
from functional_tests.base import FunctionalTest

import time


class SearchTest(FunctionalTest):

    def rebuild_index(self):
        call_command('rebuild_index', verbosity=0, interactive=False)

    def test_two_words_searched_return_correct_objects(self):
        self.rebuild_index()

        # A researcher is delighted with the NED Portal. She decides to
        # search for experiments that contains "Braquial Plexus" in whatever
        # part of the portal. The search engine is complex. Some of its
        # facilities consists in ignoring upper/lower case letters, search for
        # terms individually and in whatever order in the sentence, too.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_id('submit_keys').click()
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)
        # The search engine searches in all the site content.
        # As there are "Braquial Plexus", "braquial plexus", "Braquial",
        # "braquial", "Plexus", and "plexus" in experiments data per se,
        # studies, groups, and study keywords, she sees in Search results
        # one list for each of them.
        search_header_title = self.browser.find_element_by_tag_name('h3').text
        self.assertEqual(search_header_title, 'Search Results')

        table = self.browser.find_element_by_id('search_experiments_table')
        rows = table.find_element_by_tag_name(
            'tbody').find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                'Brachial Plexus' for row in rows)
        )
        self.assertTrue('Brachial plexus' in any(
            row.find_elements_by_tag_name('td')[1].text) for row in rows
                        )

        # As she clicks in all of the itens of that lists, she is redirected
        # the corresponding experiment detail view directly at the point
        # whose search found the terms. These terms are hilighted.
