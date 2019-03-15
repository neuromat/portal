from django.db.models import Count

from experiments.tests.tests_helper import create_experiment
from functional_tests.base import FunctionalTest


class NewVisitorTest(FunctionalTest):

    def test_can_view_home_page_basic(self):
        # In top of page she sees a link to login in the system
        login_link = self.browser.find_element_by_id('login-language').text
        self.assertIn('Log In', login_link)

        # She notices the page title and header mention
        # Neuroscience Experiments Database
        self.assertIn('Neuroscience Experiments Database', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Neuroscience Experiments Database', header_text)

        # She sees that in header bunner there is a search box inviting her
        # to type terms/words that will be searched in the portal
        # Obs.: 'id_q' is the id name that haystack search system uses
        searchbox = self.browser.find_element_by_id('id_q')
        self.assertEqual(
            searchbox.get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )
        # Bellow the search box there is a select box with a placeholder
        # telling her that she can select experiments that has EEG, TMS,
        # EMG, Gokeeper game fase etc., experiment elements that will
        # determine if an experiment will be searched or not.
        selectbox = self.browser.find_element_by_id('filter_box')
        options = selectbox.find_elements_by_tag_name('option')
        # TODO: see how to test placeholder
        # placeholder = options[0]
        # self.assertEqual(
        #     placeholder.text,
        #     'Select one or more list itens to filter experiments that has:'
        # )

        # The select box options are: EEG, TMS, EMG, Goalkeeper game
        # fase, Cinematic measures, Stabilometry, Answer time, Psychophysical
        # measures, Verbal answer, Psychometric scales, Unitary register
        self.assertTrue(any(option.text == 'EEG' for option in options))
        self.assertTrue(any(option.text == 'TMS' for option in options))
        self.assertTrue(any(option.text == 'EMG' for option in options))
        self.assertTrue(
            any(option.text == 'Goalkeeper game phase' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Kinematic measures' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Stabilometry' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Response time' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Psychophysical measures' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Verbal response' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Psychometric scales' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Unit recording' for option in options)
        )
        self.assertTrue(
            any(option.text == 'Multiunit recording' for option in options)
        )
        # As there are experiments sended to Portal, she sees the home
        # page have a list of experiments in a table.
        # She reads in "List of Experiments" in the table title.
        table_title = self.browser.find_element_by_id(
            'id_table_title').find_element_by_tag_name('h2').text
        self.assertEqual('List of Experiments', table_title)

        # She sees a list of experiments with columns: Title, Description,
        # Participants, Version
        table = self.browser.find_element_by_id('id_experiments_table')
        row_headers = table.find_element_by_tag_name(
            'thead').find_element_by_tag_name('tr')
        col_headers = row_headers.find_elements_by_tag_name('th')
        self.assertTrue(col_headers[0].text == 'Title')
        self.assertTrue(col_headers[1].text == 'Description')
        self.assertTrue(col_headers[2].text == 'Participants')
        self.assertTrue(col_headers[3].text == 'Version')

        # She sees the content of the list
        rows = table.find_element_by_tag_name('tbody')\
            .find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                self.experiment.title for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[1].text ==
                self.experiment.description for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[2].text ==
                str(self.experiment.groups.aggregate(Count(
                    'participants'))['participants__count']) +
                ' in ' + str(self.experiment.groups.count()) +
                ' groups' for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[3].text ==
                str(self.experiment.version) for row in rows)
        )

        # She notices that in the footer there is information
        # about ways of contact institution.
        footer_contact = self.browser.find_element_by_id('id_footer_contact')
        footer_header_text = footer_contact.find_element_by_tag_name('h4').text
        self.assertIn('CONTACT', footer_header_text)
        footer_content = footer_contact.find_element_by_id(
            'id_footer_contact').text
        self.assertIn('Address:', footer_content)
        self.assertIn('Matão St., 1010 - Cidade Universitária - São Paulo - '
                      'SP - Brasil. 05508-090.', footer_content)
        self.assertIn('Phone:', footer_content)
        self.assertIn('+55 11 3091-1717', footer_content)
        self.assertIn('Email:', footer_content)
        self.assertIn('neuromat@numec.prp.usp.br', footer_content)
        footer_license_text = self.browser.find_element_by_id(
            'id_footer_license').text
        self.assertIn('This site content is licensed under a Creative Commons '
                      'Attributions 4.0', footer_license_text)

    def test_can_view_home_page_when_there_is_new_version_not_approved(self):
        ##
        # Create a new version for self.experiment
        ##
        exp_new_version = create_experiment(1, owner=self.experiment.owner)
        exp_new_version.nes_id = self.experiment.nes_id
        exp_new_version.version = self.experiment.version + 1
        exp_new_version.save()

        ##
        # We have to refresh page to reflect the inclusion of the new
        # experiment version
        ##
        self.browser.refresh()

        # Josenilda is in Portal home page and see the list of experiments
        # approved. As there is one experiment approved and a new version of
        # the same experiment that has to be analysed by a trustee, she sees
        # the last approved version in the list
        table = self.browser.find_element_by_id('id_experiments_table')
        rows = table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                self.experiment.title for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[1].text ==
                self.experiment.description for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[2].text ==
                str(self.experiment.groups.aggregate(Count(
                    'participants'))['participants__count']) +
                ' in ' + str(self.experiment.groups.count()) +
                ' groups' for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[3].text ==
                str(self.experiment.version) for row in rows)
        )

    def test_view_404_http_status_code_when_trying_access_not_existent_page(self):
        # Josenilda is trying to access her experiment that she recently
        # sent to Portal, but she types the URL address incorrectly in
        # Browser, so she sees a 404 error page
        broken_url = self.experiment.slug[:-3]
        self.browser.get(self.live_server_url + '/experiments/' + broken_url)
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Not Found', body.text)
