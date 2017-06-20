import time

from experiments.models import Experiment
from functional_tests.base import FunctionalTest


class ExperimentDetailTest(FunctionalTest):

    def test_can_view_detail_page(self):
        experiment = Experiment.objects.filter(status=Experiment.APPROVED).first()
        self.browser.get(self.live_server_url)

        # The new visitor is in home page and see the list of experiments.
        # She clicks in first "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_link_text('View').click()  # TODO:
        # really gets first element?
        time.sleep(1)

        # She sees a new page with a header title: Open Database
        # for Experiments in Neuroscience.
        page_header_text = self.browser.find_element_by_tag_name('h2').text
        self.assertIn('Open Database for Experiments in Neuroscience',
                      page_header_text)

        # In header she notices three elements besides header title:
        # Experiment title, experiment detail, and a button to go back home
        # page.
        experiment_title = self.browser.find_element_by_id(
            'id_detail_title').text
        self.assertEqual(experiment.title, experiment_title)
        link_home = self.browser.find_element_by_id('id_link_home').text
        self.assertIn('Back Search', link_home)
        experiment_description = self.browser.find_element_by_id(
            'id_detail_description').text
        self.assertEqual(experiment.description, experiment_description)

        # Right bellow she sees the study that the experiment belongs to
        # at left, and if data acquisition was finished, at right
        study_text = self.browser.find_element_by_id('id_detail_study').text
        self.assertIn('Related study: ' + experiment.study.title, study_text)
        data_acquisition_text = self.browser.find_element_by_id(
            'id_detail_acquisition').text
        self.assertIn('Data acquisition not finished yet',
                      data_acquisition_text)

        # In right side bellow the data acquisition alert, she sees a link
        # to download of data
        link_download = self.browser.find_element_by_id(
            'id_link_download').text
        self.assertIn('Download data', link_download)

        # She clicks in Related study link and see a modal with Study data
        self.browser.find_element_by_link_text(experiment.study.title).click()
        time.sleep(1)
        # The modal has the study title and the study description
        study_title = self.browser.find_element_by_id('modal_study_title').text
        self.assertIn(experiment.study.title, study_title)
        study_description = self.browser.find_element_by_id(
            'study_description').text
        # It indicates that the study was made by a researcher
        self.assertIn(experiment.study.description, study_description)
        study_researcher = self.browser.find_element_by_id(
            'study_researcher').text
        self.assertIn('Researcher:', study_researcher)
        self.assertIn(experiment.study.researcher.name, study_researcher)
        # The study has a start and end date
        study_start_date = self.browser.find_element_by_id(
            'study_startdate').text
        self.assertIn('Start date:', study_start_date)
        # Obs.: code line right below is only to conform to study_start_date
        # format in browser
        self.assertIn(experiment.study.start_date.strftime("%B %d, %Y")
                      .lstrip("0").replace(" 0", " "), study_start_date)
        study_end_date = self.browser.find_element_by_id(
            'study_enddate').text
        self.assertIn('End date:', study_end_date)
        if experiment.study.end_date:
            self.assertIn(experiment.study.end_date.strftime("%B %d, %Y"),
                          study_end_date)
        else:
            self.assertIn(str(None), study_end_date)
        # Right below there is a relation of contributors of the study,
        # the contributor's team and coordinator
        study_contributors = self.browser.find_element_by_id(
            'study_contributors').text
        self.assertIn('Contributors:', study_contributors)
        table_contributors = self.browser.find_element_by_id(
            'table_contributors')
        row_headers_contrib = table_contributors.find_element_by_tag_name(
            'thead').find_element_by_tag_name('tr')
        col_headers_contrib = row_headers_contrib.find_elements_by_tag_name(
            'th')
        self.assertTrue(col_headers_contrib[0].text == 'Person')
        self.assertTrue(col_headers_contrib[1].text == 'Team')
        self.assertTrue(col_headers_contrib[2].text == 'Coordinator')
        # She sees the content of contributors list
        rows = table_contributors.find_element_by_tag_name(
            'tbody').find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                experiment.study.collaborators.first().name for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[1].text ==
                experiment.study.collaborators.first().team for row in
                rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[2].text ==
                str(experiment.study.collaborators.first().coordinator)
                for row in rows)
        )

        self.fail('Finish this test!')
