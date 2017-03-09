from selenium import webdriver
import unittest


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):

        # A neuroscience researcher discovered a new site that
        # provides a data base with neuroscience experiments.
        # She goes to checkout its home page
        self.browser.get('http://localhost:8000')

        # She notices the page title and header mention
        # Neuroscience Experiments Database
        set.assertIn('Neuroscience Experiments Database', self.browser.title)
        self.fail ('Finish the test!')

    # She sees the home page have a list of experiments
    # and click one one of that to check it out

    # She see that there is a search box in top of page.
    # So, she types in input search box:
    # "Brachial Plexus" and wait to see the results.

    # Then she see that some entries returned that
    # supposely has "Brachial Plexus" string in one
    # or more fields

if __name__ == '__main__':
    unittest.main(warnings='ignore')
