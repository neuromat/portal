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
        self.assertIn('Neuroscience Experiments Database', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('<h1>').text
        self.assertIn('Neuroscience Experiments Database', header_text) 

        # She sees the home page have a list of experiments
        # and click one one of that to check it out

        # She sees that there is a search box in top of page.
        searchbox = self.browser.find_element_by_id('id_searchbox')
        self.assertEqual(
            searchbox.get_attribute('placeholder'),
            'Enter a search text'
        )

        # She types in input search box:
        # "Brachial Plexus Experiment" and wait to see the results.
        searchbox.send_keys('Brachial Plexus Experiment')
        
        # Then she hits enter, and wait for results
        searchbox.send_keys(Keys.ENTER)
        time.sleep(1)

        # We consider, by now, that exists a row with one field containing
        # the string "Brachial Plexus Experiment"
        table = self.browser.find_element_by_id('id_results_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(
            any(row.text == 'Brachial Plexus Experiment' for row in rows)
        )

        self.fail('Finish the test!')


if __name__ == '__main__':
    unittest.main(warnings='ignore')
