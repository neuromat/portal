from django.core.management import call_command
from selenium.webdriver.common.keys import Keys
from functional_tests.base import FunctionalTest

import time


class SearchTest(FunctionalTest):

    @staticmethod
    def rebuild_index():
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
        # As there are "Braquial Plexus", "braquial plexus" in experiments
        # data per se, and the two words are also found separated,
        # like 'brachial ... plexus' and 'plexus ... brachial', for intance, in
        # studies, groups, and study keywords, she sees in Search results
        # one list for each of them.
        # One experiment has 'Brachial Plexus' in title, other has 'Brachial
        # plexus' in description
        search_header_title = self.browser.find_element_by_tag_name('h3').text
        self.assertEqual(search_header_title, 'Search Results')

        table = self.browser.find_element_by_id('search_experiments_table')
        rows = table.find_element_by_tag_name(
            'tbody').find_elements_by_tag_name('tr')
        self.assertTrue(any('Brachial Plexus' in row.text for row in rows))
        self.assertTrue(any('Brachial plexus' in row.text for row in rows))
        # There's an experiment whose study has the word 'brachial' in study
        # description. When there are matches in other models data besides
        # experiment, a new line in the results displays other models'
        # matches, below the experiment that model pertains.
        rows_other_models = \
            self.browser.find_elements_by_class_name(
                'matches-not-experiment'
            )
        self.assertTrue(any('Study:' in row.text for row in rows_other_models))
        self.assertTrue(
            any('brachial' in row.text for row in rows_other_models)
        )

        # There are two groups with the string 'Plexus brachial' in
        # description groups
        self.assertTrue(
            any('Groups:' in row.text for row in rows_other_models)
        )
        self.assertTrue(
            any('Plexus brachial' in row.text for row in rows_other_models)
        )

        # As she clicks in all of the itens of that lists, she is redirected
        # the corresponding experiment detail view directly at the point
        # whose search found the terms. These terms are hilighted. TODO?
        self.fail('Finish this test!')
