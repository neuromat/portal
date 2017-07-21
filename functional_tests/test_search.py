import time
from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from functional_tests.base import FunctionalTest


class SearchTest(FunctionalTest):
    pass
    # TODO: disabled by now, untile we have defined the search tool
    # def test_simple_word_returns_experiments(self):
    #     self.browser.get(self.live_server_url)
    #
    #     # A researcher is interested in finding experiments that contains
    #     # Plexus in title. She sees that NEP system has a search box to
    #     # search experiments. She types plexus in it.
    #     search_form = self.browser.find_element_by_id('search_form')
    #     search_box = self.browser.find_element_by_id(
    #         'search_box')
    #     search_box.send_keys('Plexus')
    #     self.browser.find_element_by_id('submit_keys').click()
    #     # search_box.send_keys(Keys.ENTER)
    #     time.sleep(1)
    #     # The system searches in title experiments and find one entry that
    #     # is displayed in Search Results
    #     search_table_title = self.browser.find_element_by_tag_name('h2').text
    #     self.assertEqual(search_table_title, 'Search Results')
    #     experiment_searched = Experiment.objects.get(title="Plexus")
    #     self.assertIn(experiment_searched.title, 'Braquial Plexus')

