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
        self.browser.find_element_by_id('submit_terms').click()
        # search_box.send_keys(Keys.ENTER)
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

        table = self.browser.find_element_by_id('search_table')
        experiment_rows = \
            table.find_elements_by_class_name('experiment_matches')
        self.assertTrue(
            any('Brachial Plexus' in row.text for row in experiment_rows)
        )
        self.assertTrue(
            any('Brachial plexus' in row.text for row in experiment_rows)
        )
        # There's an experiment whose study has the word 'brachial' in study
        # description, and 'brachial plexus' in one of the study keywords -
        # when there are matches in other models data besides
        # experiment, a new line in the results displays other models'
        # matches, below the experiment that model pertains.
        study_rows = \
            self.browser.find_elements_by_class_name('study_matches')
        self.assertTrue(any('Study:' in row.text for row in study_rows))
        self.assertTrue(any('brachial' in row.text for row in study_rows))
        self.assertTrue(
            any('brachial plexus' in row.text for row in study_rows)
        )

        # There's one group with the string 'Plexus brachial' in
        # group description, and 'brachial Plexus' in group inclusion criteria
        group_rows = self.browser.find_elements_by_class_name('group_matches')
        self.assertTrue(any('Groups:' in row.text for row in group_rows))
        self.assertTrue(
            any('Plexus brachial' in row.text for row in group_rows)
        )
        self.assertTrue(
            any('brachial Plexus' in row.text for row in group_rows)
        )

        # The researcher now wishes to search for a study that has as
        # collaborator a coleague of her, called Pero Vaz.
        # She types 'Pero Vaz' in search box and hits Enter.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Pero Vaz')
        # self.browser.find_element_by_id('submit_terms').click()
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)
        # She sees that there is one Study whose one of collaborator is Pero
        # Vaz.
        study_rows = \
            self.browser.find_elements_by_class_name('study_matches')
        self.assertTrue(any('Pero Vaz' in row.text for row in study_rows))

        self.fail('Finish this test!')
