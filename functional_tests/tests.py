from selenium import webdriver

import unittest


class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_view_initial_page(self):

        # A neuroscience researcher discovered a new site that
        # provides a data base with neuroscience experiments.
        # She goes to checkout its home page
        self.browser.get('http://localhost:8000')

        # She notices the page title and header mention
        # Neuroscience Experiments Database
        self.assertIn('Neuroscience Experiments Database', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Neuroscience Experiments Database', header_text)

        # She sees the home page have a list of experiments
        # and click in one of that to check it out

        self.fail('Finish the test!')


if __name__ == '__main__':
    unittest.main(warnings='ignore')
