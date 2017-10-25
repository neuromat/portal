import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment, Questionnaire, Step
from functional_tests.base import FunctionalTest


class ExperimentDetailTest(FunctionalTest):

    def wait_for_detail_page_charge(self):
        ##
        # First we wait for the page completely charge. For this we
        # guarantee an element of the page is there. As any of the
        # statistics, groups, and settings tab is always there, we wait for
        # Group tab.
        ##
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Groups').text,
            'Groups'
        ))

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

        # She sees a new page with a header title: Open Database
        # for Experiments in Neuroscience.
        self.wait_for(lambda: self.assertIn(
            'Open Database for Experiments in Neuroscience',
            self.browser.find_element_by_tag_name('h2').text
        ))

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

        # The modal has the study title and the study description
        self.wait_for(lambda: self.assertIn(
            experiment.study.title,
            self.browser.find_element_by_id('modal_study_title').text
        ))

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

        # She hits ESC to exit Study modal and clicks the Groups tab
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
        code_not_recognized_instances = 0
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
            code_not_recognized_instances = code_not_recognized_instances + \
                group.inclusion_criteria.filter(
                        description='Code not recognized'
                ).count()
        code_not_recognized_in_template = \
            len(self.browser.find_elements_by_class_name('not-recognized'))
        self.assertEqual(
            code_not_recognized_instances, code_not_recognized_in_template
        )

        # Finally, at right of each group information there is a button
        # written 'Details'. She clicks on the first link and the panel
        # expands displaying textual representation of the experimental
        # protocol.
        group = experiment.groups.first()
        link_details = self.browser.find_element_by_link_text('Details')
        link_details.click()

        self.wait_for(lambda: self.assertIn(
            'Textual description',
            self.browser.find_element_by_id('collapse' + str(group.id)).text
        ))

        self.assertIn(
            group.experimental_protocol.textual_description,
            self.browser.find_element_by_id('collapse' + str(group.id)).text
        )

        # She notices that the protocol experiment image is a link. When she
        # clicks on it, a modal is displayed with the full image.
        self.browser.find_element_by_id('protocol_image').click()
        ##
        # We wait for modal pops up
        ##
        self.wait_for(lambda: self.assertIn(
            'Graphical representation',
            self.browser.find_element_by_id('modal_protocol_title').text
        ))

        modal = self.browser.find_element_by_id('protocol_image_full')
        protocol_image_path = modal.find_element_by_tag_name(
            'img'
        ).get_attribute('src')
        self.assertTrue(
            '/media/' +
            str(experiment.groups.first().experimental_protocol.image),
            protocol_image_path
        )

    def test_can_view_questionaire_tab(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in second "View" link and is redirected to experiment
        # detail page
        # TODO: frequently fails to catch second link
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment.slug) + "/']"
        ).click()

        # There's a tab written Questionnaires
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Questionnaires').text,
            'Questionnaires'
        ))

    def test_does_not_display_questionnaire_tab_if_there_are_not_questionnaires(self):
        ##
        # We pick an experiment without questionnaires. The second approved
        # experiment hasn't questionnaires steps in any experiment protocol
        # of no one group. See tests helper
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).all()[1]

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in second "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        # As there are no questionnaires for this experiment, she can't see
        # the Questionnaires tab and Questionnaires content
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_link_text('Questionnaires')

    def test_can_view_group_questionnaires_and_questionnaires_titles(self):
        ##
        # We've created Questionnaire data in tests helper from a Sample
        # of a questionnaire from NES, in csv format. The Questionnaire is
        # associated with a group of the last experiment created in tests
        # helper.
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        ##
        # We get groups objects with questionnaire steps
        ##
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = experiment.groups.filter(steps__in=q_steps)

        # When the new visitor clicks in the Questionnaires tab, she sees
        # the groups questionnaires and the questionnaires' titles as
        # headers of the questionnaires contents
        self.browser.find_element_by_link_text('Questionnaires').click()
        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).text
        if groups_with_qs.count() == 0:
            self.fail('There are no groups with questionnaires. Have you '
                      'been created the questionnaires in tests helper?')
        for group in groups_with_qs:
            self.assertIn(
                'Questionnaires for group ' + group.title,
                questionnaires_content
            )
            for step in group.steps.filter(type=Step.QUESTIONNAIRE):
                questionnaire = Questionnaire.objects.get(step_ptr=step)
                questionnaire_language = \
                    questionnaire.q_languages.get(
                        language_code='en'
                    )
                self.assertIn(
                    'Questionnaire ' + questionnaire_language.survey_name,
                    questionnaires_content
                )

    def test_detail_button_expands_questionnaire_to_display_questions_and_answers(self):
        ##
        # We've created Questionnaire data in tests helper from a Sample
        # of a questionnaire from NES, in csv format
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # When the new visitor visits an experiment that has questionnaires,
        # in right side of each questionnaire title that is a 'Detail'
        # button. When she clicks on it, the questionnaire expand to display
        # the questions and answers.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        self.browser.find_element_by_link_text('Questionnaires').click()

        button_details = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).find_element_by_link_text('Details')
        button_details.click()
        time.sleep(1)
        button_details.click()
        time.sleep(1)  # just to see better on the browser, before page closes

        self.assertEqual(button_details.text, 'Details')

    def test_can_view_questionnaires_content(self):
        ##
        # We've created three questionnaires in an experiment, two are from one
        # group and one are from another group. We test questions and
        # answers from this three questionnaires. See tests helper.
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in second "View" link and is redirected to experiment
        # detail page.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        # When the new visitor clicks in the Questionnaires tab, then click
        # in 'Details' button of the Questionnaires sections she sees
        # the questionnaires' content as a series of questions and answers
        self.browser.find_element_by_link_text('Questionnaires').click()
        questionnaires = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).find_elements_by_link_text('Details')
        for q in questionnaires:
            q.click()
        time.sleep(0.5)

        # TODO: click on the 'Details' buttons just for simulate user
        # TODO: interaction, as the questionnaires' content is in html page
        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        ##
        # Sample asserts for first questionnaire.
        ##
        self.assertIn('History of fracture?', questionnaires_content)
        self.assertIn('Have you ever had any orthopedic surgery?',
                      questionnaires_content)
        self.assertIn('Did you have any nerve surgery?',
                      questionnaires_content)
        self.assertIn('Identify the event that led to the trauma of your '
                      'brachial plexus. You can mark more than one event.',
                      questionnaires_content)
        self.assertIn('Did you have any fractures associated with the injury?',
                      questionnaires_content)
        self.assertIn('The user enters a date in a date field',
                      questionnaires_content)

        ##
        #  Sample asserts for second questionnaire
        ##
        self.assertIn('What side of the injury?', questionnaires_content)
        self.assertIn('Institution of the Study', questionnaires_content)
        self.assertIn('The user enters a free text',
                      questionnaires_content)
        self.assertIn('Injury type (s):', questionnaires_content)
        self.assertIn('Thrombosis', questionnaires_content)
        self.assertIn('Attach exams.', questionnaires_content)
        self.assertIn('The user uploads file(s)',
                      questionnaires_content)
        self.assertIn('The user answers yes or not', questionnaires_content)

        ##
        # Sample asserts for third questionnaire
        ##
        self.assertIn('Refere dor após a lesão?', questionnaires_content)
        self.assertIn('EVA da dor principal:', questionnaires_content)
        self.assertIn('Qual região apresenta alteração do trofismo?',
                      questionnaires_content)
        self.assertIn('Atrofia', questionnaires_content)
        self.assertIn('Qual(is) artéria(s) e/ou vaso(s) foram acometidos?',
                      questionnaires_content)
        self.assertIn('Artéria axilar', questionnaires_content)
        self.assertIn('Quando foi submetido(a) à cirurgia(s) de plexo '
                      'braquial (mm/aaaa)?', questionnaires_content)

    def test_invalid_questionnaire_displays_message(self):
        ##
        # We've created invalid Questionnaire data in tests helper in first
        # experiment approved
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).first()

        # The new visitor is at home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        # As there's a questionnaire from a group that has the wrong number
        # of columns, when the new visitor clicks in Questionnaires tab she
        # sees a message telling her that something is wrong with that
        # questionnaire.
        self.browser.find_element_by_link_text('Questionnaires').click()

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).text

        self.assertIn('This questionnaire is in invalid format, and can\'t '
                      'be displayed', questionnaires_content)

    def test_can_see_all_language_links_of_questionnaires_if_available(self):
        ##
        # We've created two questionnaires in tests helper from a Sample
        # of questionnaires from NES, in csv format. The questionnaires are
        # associated with a group of the last approved experiment created in
        # tests helper. One of the questionnaires has three languages, English,
        # French, and Brazilian Portuguese. The other has two languages,
        # English and German. Besides, we have a third questionnaire created
        # in tests helper that has only the English language associated to it.
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_charge()

        # When the new visitor clicks in the Questionnaires tab, she sees,
        # below questionnaire titles, a sequence of buttons indicating the
        # available languages of the questionnaires
        self.browser.find_element_by_link_text('Questionnaires').click()

        ##
        # We get all the elements that contains button languages
        # and your available languages
        ##
        lang_elements = self.browser.find_elements_by_class_name(
            'questionnaire-languages'
        )
        ##
        # As in the template the order of questionnaires varies from one
        # access to another, we join all questionnaires language codes in
        # one list to make assertions below
        ##
        q_lang_codes = ''
        for lang in lang_elements:
            q_lang_codes = q_lang_codes + ' ' + lang.text

        self.assertEqual(q_lang_codes.count('en'), 3)
        self.assertEqual(q_lang_codes.count('fr'), 1)
        self.assertEqual(q_lang_codes.count('pt-br'), 1)
        self.assertEqual(q_lang_codes.count('de'), 1)
