import time

from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from functional_tests.base import FunctionalTest


class ExperimentDetailTest(FunctionalTest):

    # TODO: break by tabs
    def test_can_view_detail_page(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The new visitor is in home page and see the list of experiments.
        # She clicks in second "View" link and is redirected to experiment
        # detail page
        # TODO: frequently fails to catch second link (see if it's solved)
        link = self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        )
        link.click()
        # list_links = self.browser.find_elements_by_link_text('View')
        # list_links[0].click()
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
        self.assertIn('Back Home', link_home)
        experiment_description = self.browser.find_element_by_id(
            'id_detail_description').text
        self.assertEqual(experiment.description, experiment_description)

        # Bellow experiment description there is a link to the project site
        # (because experiment has that data posted via api)
        ethics_commitee_project_info = \
            self.browser.find_element_by_link_text('Project Info')
        self.assertEqual(
            experiment.project_url,
            ethics_commitee_project_info.get_attribute('href')
        )

        # At the right side there is a warning telling that the data
        # acquisition was finished or not
        data_acquisition_text = self.browser.find_element_by_id(
            'id_detail_acquisition').text
        if experiment.data_acquisition_done:
            self.assertIn('Data acquisition was completed',
                          data_acquisition_text)
        else:
            self.assertIn('Data acquisition was not completed',
                          data_acquisition_text)

        # Right bellow she sees the study that the experiment belongs to
        # at left
        study_text = self.browser.find_element_by_id('id_detail_study').text
        self.assertIn('From study: ' + experiment.study.title, study_text)

        # In right side bellow the data acquisition alert, she sees a button
        # to download of data
        button_download = self.browser.find_element_by_id(
            'button_download')
        self.assertEqual(
            'Download experiment data',
            button_download.text
        )

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
        self.assertIn(experiment.study.start_date.strftime("%b. %d, %Y")
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
        # Finally, in the study modal, she sees a list of keywords
        # associated with the study
        keywords_text = self.browser.find_element_by_id('keywords').text
        for keyword in experiment.study.keywords.all():
            self.assertIn(keyword.name, keywords_text)

        ##
        # Testing Statistics, Groups and Settings
        ##

        # She hit ESC to exit Study modal and clicks the Groups tab
        study_modal = self.browser.find_element_by_id('study_modal')
        study_modal.send_keys(Keys.ESCAPE)
        time.sleep(1)
        self.browser.find_element_by_link_text('Groups').click()
        # In Groups tab she can see a list of the groups associated with
        # this experiment with: group's title, description, the protocol
        # experiment image (if it has one), and the number of participants
        # in that group. There is also the information criteria that was
        # used to include each group.
        groups_tab_content = self.browser.find_element_by_id('groups_tab').text
        for group in experiment.groups.all():
            self.assertIn(group.title, groups_tab_content)
            self.assertIn(group.description, groups_tab_content)
            self.assertIn(str(group.participants.all().count()) +
                          ' participants', groups_tab_content)
            if group.inclusion_criteria.all().count() > 0:
                self.assertIn('Inclusion criterias:', groups_tab_content)
                for ic in group.inclusion_criteria.all():
                    self.assertIn(ic.code + ' - ' + ic.description,
                                  groups_tab_content)
        # Finally, at right of each group information there is a button
        # written 'Details'. She clicks on the first link and the panel
        # expands displaying textual representation of the experimental
        # protocol.
        group = experiment.groups.first()
        link_details = self.browser.find_element_by_link_text('Details')
        link_details.click()
        time.sleep(1)
        expanded_panel = self.browser.find_element_by_id('collapse' +
                                                         str(group.id)).text
        self.assertIn('Textual description', expanded_panel)
        self.assertIn(group.experimental_protocol.textual_description,
                      expanded_panel)

        # She notices that the protocol experiment image is a link. When she
        # clicks on it, a modal is displayed with the full image.
        self.browser.find_element_by_id('protocol_image').click()
        time.sleep(1)
        modal = self.browser.find_element_by_id('protocol_image_full')
        modal_title = self.browser.find_element_by_class_name(
            'modal-title').text
        self.assertIn(modal_title, 'Graphical representation')
        protocol_image_path = modal.find_element_by_tag_name(
            'img').get_attribute('src')
        self.assertTrue(
            '/media/' + str(experiment.groups.first()
                            .experimental_protocol.image),
            protocol_image_path
        )
