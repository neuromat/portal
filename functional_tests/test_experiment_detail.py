import os
import tempfile
import time
import zipfile
from random import choice
from unittest import skip

import shutil

from django.conf import settings
from django.test import override_settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from downloads.views import DOWNLOAD_ERROR_MESSAGE, download_create
from experiments.models import Questionnaire, Step, Gender, Experiment
from experiments.tests.tests_helper import create_group, \
    create_participant, \
    remove_selected_subdir, create_experimental_protocol, \
    create_questionnaire, create_questionnaire_language, create_study, \
    create_eeg_data, create_eeg_setting, \
    create_valid_questionnaires, create_publication, \
    create_experiment_researcher, create_researcher, \
    create_trustee_user, create_next_version_experiment, \
    create_ethics_committee_info, create_genders, create_step, \
    create_questionnaire_responses
from functional_tests.base import FunctionalTest


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class ExperimentDetailTest(FunctionalTest):

    def setUp(self):
        create_trustee_user('claudia')
        create_trustee_user('roque')
        super(ExperimentDetailTest, self).setUp()

    def _access_experiment_detail_page(self, experiment):
        # The new visitor is in home page and see the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        link = self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        )
        link.click()

    # TODO: break by tabs
    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_can_view_detail_page(self):
        study = create_study(1, self.experiment)
        create_ethics_committee_info(self.experiment)
        create_researcher(study)
        g1 = create_group(1, self.experiment)
        create_experimental_protocol(g1)
        create_group(1, self.experiment)

        self._access_experiment_detail_page(self.experiment)

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
        self.assertEqual(self.experiment.title, experiment_title)
        link_home = self.browser.find_element_by_id('id_link_home').text
        self.assertIn('Back Home', link_home)
        experiment_description = self.browser.find_element_by_id(
            'id_detail_description').text
        self.assertEqual(self.experiment.description, experiment_description)

        # Bellow experiment description there is a link to the project site
        # (because experiment has that data posted via api)
        ethics_commitee_project_info = \
            self.browser.find_element_by_link_text('Project Info')
        self.assertEqual(
            self.experiment.project_url,
            ethics_commitee_project_info.get_attribute('href')
        )

        # At the right side there is a warning telling that the data
        # acquisition was finished. if it was not finished, display number
        # of participants until now.
        data_acquisition_text = self.browser.find_element_by_id(
            'id_detail_acquisition').text
        if self.experiment.data_acquisition_done:
            self.assertIn(
                'Data acquisition was completed', data_acquisition_text
            )
        else:
            total_participants = 0
            for group in self.experiment.groups.all():
                total_participants += group.participants.count()
            self.assertIn('Current number of participants: '
                          + str(total_participants) + ' (and counting)',
                          data_acquisition_text)

        # Right bellow she sees the study that the experiment belongs to
        # at left
        study_text = self.browser.find_element_by_id('id_detail_study').text
        self.assertIn('From study: ' + self.experiment.study.title, study_text)

        # She clicks in Related study link and sees a modal with Study data
        self.browser.find_element_by_link_text(self.experiment.study.title).click()

        # The modal has the study title and the study description
        self.wait_for(lambda: self.assertIn(
            self.experiment.study.title,
            self.browser.find_element_by_id('modal_study_title').text
        ))

        study_description = self.browser.find_element_by_id(
            'study_description').text
        # It indicates that the study was made by a researcher
        self.assertIn(self.experiment.study.description, study_description)
        study_researcher = self.browser.find_element_by_id(
            'study_researcher').text
        self.assertIn('Researcher:', study_researcher)
        self.assertIn(
            self.experiment.study.researcher.first_name + ' ' +
            self.experiment.study.researcher.last_name,
            study_researcher
        )
        # The study has a start and end date
        study_start_date = self.browser.find_element_by_id(
            'study_startdate').text
        self.assertIn('Start date:', study_start_date)
        self.assertIn(
            self.experiment.study.start_date.strftime("%B %d, %Y"),
            study_start_date
        )
        study_end_date = self.browser.find_element_by_id(
            'study_enddate').text
        self.assertIn('End date:', study_end_date)
        if self.experiment.study.end_date:
            self.assertIn(self.experiment.study.end_date.strftime("%B %d, %Y"),
                          study_end_date)

        # Finally, in the study modal, she sees a list of keywords
        # associated with the study
        keywords_text = self.browser.find_element_by_id('keywords').text
        for keyword in self.experiment.study.keywords.all():
            self.assertIn(keyword.name, keywords_text)

        ##
        # Testing Statistics, Groups and Settings
        ##

        # She hits ESC to exit Study modal and clicks the Groups tab
        study_modal = self.browser.find_element_by_id('study_modal')
        study_modal.send_keys(Keys.ESCAPE)
        time.sleep(1)  # TODO: eliminate implicit wait
        self.browser.find_element_by_link_text('Groups').click()
        # In Groups tab she can see a list of the groups associated with
        # this experiment with: group's title, description, the protocol
        # experiment image (if it has one), and the number of participants
        # in that group. There is also the information criteria that was
        # used to include each group.
        groups_tab_content = self.browser.find_element_by_id('groups_tab').text
        code_not_recognized_instances = 0
        for group in self.experiment.groups.all():
            self.assertIn(group.title, groups_tab_content)
            self.assertIn(group.description, groups_tab_content)
            self.assertIn(str(group.participants.all().count()) +
                          ' participants', groups_tab_content)
            if group.inclusion_criteria.all().count() > 0:
                self.assertIn('Inclusion criterias:', groups_tab_content)
                for ic in group.inclusion_criteria.all():
                    self.assertIn(ic.code + ' - ' + ic.description,
                                  groups_tab_content)
            code_not_recognized_instances = \
                code_not_recognized_instances + \
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
        # protocol
        group = self.experiment.groups.first()
        link_details = self.browser.find_element_by_xpath(
            "//a[@href='#collapse_group" + str(group.id) + "']")
        link_details.click()

        self.wait_for(lambda: self.assertIn(
            'Textual description',
            self.browser.find_element_by_id('collapse_group' + str(group.id)).text
        ))

        self.assertIn(
            group.experimental_protocol.textual_description,
            self.browser.find_element_by_id('collapse_group' + str(group.id)).text
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
            str(self.experiment.groups.first().experimental_protocol.image),
            protocol_image_path
        )

        shutil.rmtree(TEMP_MEDIA_ROOT)

    def test_can_see_publications_link(self):
        create_publication(self.experiment)
        create_publication(self.experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(self.experiment.slug) + "/']"
        ).click()

        # As last approved experiment has a publication associated with it,
        # she sees a link to publications below the experiment description
        # area, at right
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Publications').text,
            'Publications'
        ))

    def test_can_see_publications_modal_with_correct_content(self):
        create_publication(self.experiment)
        create_publication(self.experiment)
        publications = self.experiment.publications.all()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(self.experiment.slug) + "/']"
        ).click()

        ##
        # IMPORTANT: it's important to wait until 'publications_modal' div
        # is visible by selenium driver before clicking in it. This is
        # because the google chart stuff in Statistics tab can delay that
        # div for some time
        ##
        self.wait_for(lambda: self.browser.find_element_by_id(
            'publications_modal'))
        publications_modal = self.browser.find_element_by_id(
            'publications_modal')

        # As last approved experiment has publications associated with it,
        # she sees a link to publications below the experiment description
        # area, at right. She clicks in it
        self.browser.find_element_by_link_text('Publications').send_keys(
            Keys.ENTER)

        self.wait_for(lambda: self.assertIn(
            'Publications', publications_modal.text
        ))
        self.wait_for(lambda: self.assertIn(
            publications.first().title, publications_modal.text
        ))
        self.wait_for(lambda: self.assertIn(
            publications.first().citation, publications_modal.text,
        ))
        self.wait_for(lambda: self.assertIn(
            publications.first().url, publications_modal.text,
        ))
        self.wait_for(lambda: self.assertIn(
            publications.last().title, publications_modal.text,
        ))
        self.wait_for(lambda: self.assertIn(
            publications.last().citation, publications_modal.text,
        ))
        self.wait_for(lambda: self.assertIn(
            publications.last().url, publications_modal.text,
        ))

    def test_publications_urls_are_links(self):
        create_publication(self.experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(self.experiment.slug) + "/']"
        ).click()

        # As last approved experiment has publications associated with it,
        # she sees a link to publications below the experiment description
        # area, at right. She clicks in it
        self.wait_for(lambda: self.browser.find_element_by_link_text(
            'Publications'
        ).click())

        for publication in self.experiment.publications.all():
            try:
                self.wait_for(
                    lambda:
                    self.browser.find_element_by_link_text(publication.url)
                )
            except NoSuchElementException:
                self.fail(publication.url + ' is not a link')

    def test_can_view_questionaire_tab(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(self.experiment.slug) + "/']"
        ).click()

        # There's a tab written Questionnaires
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Questionnaires').text,
            'Questionnaires'
        ))

    def test_does_not_display_questionnaire_tab_if_there_are_not_questionnaires(self):
        # The new visitor is in home page and sees the list of experiments.
        # She clicks in second "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # As there are no questionnaires for this experiment, she can't see
        # the Questionnaires tab and Questionnaires content
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_link_text('Questionnaires')

    def test_can_view_group_questionnaires_and_questionnaires_titles(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])

        ##
        # get groups objects with questionnaire steps
        ##
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = self.experiment.groups.filter(steps__in=q_steps)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # When the new visitor clicks in the Questionnaires tab, she sees
        # the groups questionnaires and the questionnaires' titles as
        # headers of the questionnaires contents
        self.browser.find_element_by_link_text('Questionnaires').send_keys(
            Keys.ENTER
        )
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
                questionnaire_language = questionnaire.q_languages.first()
                self.assertIn(
                    'Questionnaire ' + questionnaire_language.survey_name,
                    questionnaires_content
                )

    def test_detail_button_expands_questionnaire_to_display_questions_and_answers(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])

        # When the new visitor visits an experiment that has questionnaires,
        # in right side of each questionnaire title is a 'Detail'
        # button. When she clicks on it, the questionnaire expand to display
        # the questions and answers.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        self.browser.find_element_by_link_text('Questionnaires').click()

        button_details = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).find_element_by_link_text('Details')
        button_details.send_keys(Keys.ENTER)

        self.assertEqual(button_details.text, 'Details')

    def test_can_view_questionnaires_content(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link corresponded to the experiment and is
        # redirected to experiment detail page.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # When the new visitor clicks in the Questionnaires tab, then click
        # in 'Details' button of the Questionnaires sections she sees
        # the questionnaires' content as a series of questions and answers
        # divided by groups of questions
        self.browser.find_element_by_link_text('Questionnaires').click()
        questionnaires = self.wait_for(
            lambda: self.browser.find_element_by_id(
                'questionnaires_tab'
            ).find_elements_by_link_text('Details')
        )
        for q in questionnaires:
            q.click()
        time.sleep(0.3)  # to catch all content
        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        ##
        # Sample asserts for first questionnaire
        #
        self.assertIn('Primeiro Grupo', questionnaires_content)
        self.assertIn('Segundo Grupo', questionnaires_content)
        self.assertIn('História de fratura?', questionnaires_content)
        self.assertIn('Já fez alguma cirurgia ortopédica?',
                      questionnaires_content)
        self.assertIn('Fez alguma cirurgia de nervo?',
                      questionnaires_content)
        self.assertIn('Identifique o evento que levou ao trauma do seu plexo '
                      'braquial. É possível marcar mais do que um evento.',
                      questionnaires_content)
        self.assertIn('Teve alguma fratura associada à lesão?',
                      questionnaires_content)

        ##
        # Sample asserts for second questionnaire
        #
        # she sees an Array (Flexible Labels) multiple texts question
        self.assertIn(
            '(This question is a matrix based on the following fields)',
            questionnaires_content
        )
        # she sees an Array (Texts) question
        self.assertIn('Questão Array (Texts)', questionnaires_content)
        # she sees an Array by column question
        self.assertIn('Questão Array by column', questionnaires_content)
        self.assertIn('Subquestion array by column 1', questionnaires_content)
        self.assertIn('Answer array by column 2', questionnaires_content)
        # she sees a Numerical Input question
        self.assertIn('Questão Numerical Input', questionnaires_content)
        self.assertIn(
            'Participant answers with a numerical value',
            questionnaires_content
        )
        # she sees a Five Point Choice question
        self.assertIn('Five Point Choice', questionnaires_content)
        # she sees an Array (5 point choice) question
        self.assertIn('Questão Array (5 point choice)', questionnaires_content)
        self.assertIn('subquestionSQ001', questionnaires_content)
        self.assertIn(
            '(For each subquestion the participant chooses a level from 1 to '
            '5 or no level)',
            questionnaires_content
        )
        # she sees a File Upload question
        self.assertIn('Attach exams.', questionnaires_content)
        self.assertIn('Participant uploads file(s)', questionnaires_content)
        # she sees an Array dual scale question
        self.assertIn('Questão Array dual scale', questionnaires_content)
        self.assertIn('Subquestion Array Dual Scale', questionnaires_content)
        self.assertIn('Answer Array dual scale', questionnaires_content)
        # she sees a Multiple choice question
        self.assertIn('Institution of the Study', questionnaires_content)
        self.assertIn('Injury type (s):', questionnaires_content)
        self.assertIn('Thrombosis', questionnaires_content)
        # she sees a List (Radio) question
        self.assertIn('What side of the injury?', questionnaires_content)
        # she sees an Array (Yes/No/Uncertain) question
        self.assertIn(
            'Questão Array (Yes/No/Uncertain)', questionnaires_content
        )
        self.assertIn('subquestionSQ002', questionnaires_content)
        self.assertIn(
            '(For each subquestion the participant chooses between Yes, No, '
            'Uncertain, No answer)',
            questionnaires_content
        )
        # she sees an Array (Increase/Same/Decrease) question
        self.assertIn(
            'Questão Array (Increase/Same/Decrease)', questionnaires_content
        )
        self.assertIn('Subquestion (I/S/D)', questionnaires_content)
        self.assertIn(
            '(For each subquestion the participant chooses between '
            'Increase, Same, Decrease)',
            questionnaires_content
        )
        # she sees a Gender question
        self.assertIn('Questão Gender', questionnaires_content)
        self.assertIn(
            'Participant chooses between Female, Male, No answer',
            questionnaires_content
        )
        # she sees a Language Switch question
        self.assertIn('Questão Language Switch', questionnaires_content)
        self.assertIn(
            'Participant chooses between predefined languages',
            questionnaires_content
        )
        # she sees a Multiple Numerical Input question
        self.assertIn(
            'Questão Multiple numerical input', questionnaires_content
        )
        self.assertIn(
            'Subquestion multiple numerical input', questionnaires_content
        )
        self.assertIn(
            '(For each subquestion the participant enters a numerical value)',
            questionnaires_content
        )
        # she sees a List With Comment question
        self.assertIn('Questão List with comment', questionnaires_content)
        self.assertIn('answer list with comments', questionnaires_content)
        self.assertIn(
            '(Participant chooses one out of the options and can fill '
            'a text box with a comment)',
            questionnaires_content
        )
        # she sees a Multiple Short Text question
        self.assertIn('Questão Multiple short text', questionnaires_content)
        self.assertIn(
            'Subquestion multiple short question', questionnaires_content
        )
        self.assertIn(
            'For each subquestion the participant enters a free text',
            questionnaires_content
        )
        # she sees a Ranking question
        self.assertIn('Questão Ranking', questionnaires_content)
        self.assertIn('Answer Ranking', questionnaires_content)
        self.assertIn(
            '(Participant ranks the options)', questionnaires_content
        )
        # she sees a Short Free Text question
        self.assertIn('Questão Short free text', questionnaires_content)
        self.assertIn(
            'Participant enters a short free text', questionnaires_content
        )
        # she sees a Huge Free Text question
        self.assertIn('Questão Huge Free Text', questionnaires_content)
        # TODO: complete with assertion for info text, like above

        # she sees a List Dropdown question
        self.assertIn('Questão List (dropdown)', questionnaires_content)
        self.assertIn('código A3', questionnaires_content)
        self.assertIn(
            '(Participant chooses one option out of a dropdown list)',
            questionnaires_content
        )
        # she sees an Array (Flexible Labels) multiple drop down question
        self.assertIn(
            'Questão Array (Flexible Labels) multiple drop down',
            questionnaires_content
        )
        self.assertIn('subquestionSQ002', questionnaires_content)
        self.assertIn(
            '(This question is a matrix based on the following '
            'fields. For each matrix cell the participant chooses '
            'one option out of a dropdown list)',
            questionnaires_content
        )
        # she sees a Yes or Not question
        self.assertIn('Participant answers yes or not', questionnaires_content)
        # she sees a Text Display question (Boiler plate question in old
        # versions of LimeSurvey)
        self.assertIn(
            'A text is displayed to the participant (user does not answer '
            'this question)',
            questionnaires_content
        )
        # she sees a Long/Huge free text question
        self.assertIn('Participant enters a free text', questionnaires_content)
        # she sees a 5 point choice question
        self.assertIn(
            'Participant chooses a level from 1 to 5 or no level',
            questionnaires_content
        )

        ##
        # Sample asserts for third questionnaire
        #
        self.assertIn('Primeiro Grupo', questionnaires_content)
        self.assertIn('Terceiro Grupo', questionnaires_content)
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

    def test_questionnaire_content_is_displayed_with_questions_in_right_order(self):
        g1 = create_group(1, self.experiment)
        q1 = create_questionnaire(1, 'q1', g1)
        ##
        # create questionnaire language data pt-br for questionnaire1
        create_questionnaire_language(
            q1,
            settings.BASE_DIR + '/experiments/tests/questionnaire1_pt-br.csv',
            # our tests helper always consider 'en' as Default Language,
            # so we create this time as 'pt-br' to test creating questionnaire
            # default language in test_api (by the moment only test_api tests
            # creating questionnaire default language; can expand testing
            # questionnaire related models)
            'pt-br'
        )

        # Shayene acessa a página de detalhes de um experimento
        self.browser.get(
            self.live_server_url + '/experiments/' + self.experiment.slug
        )

        # When the new visitor clicks in the Questionnaires tab, then click
        # in 'Details' button of the Questionnaires sections she sees
        # the questionnaires' content as a series of questions and answers
        # divided by groups of questions
        self.browser.find_element_by_link_text('Questionnaires').click()
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'questionnaires_tab'
            ).find_element_by_link_text('Details').click()
        )

        # wait for accordion to spawn
        time.sleep(0.3)

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        # assert for questions in right order
        self.assertRegex(
            questionnaires_content,
            'Primeiro Grupo[\s\S]+História de fratura[\s\S]+'
            'Já fez alguma cirurgia ortopédica[\s\S]+'
            'Fez alguma cirurgia de nervo[\s\S]+'
            'História prévia de dor[\s\S]+'
            'Identifique o evento que levou ao trauma do seu plexo '
            'braquial[\s\S]+'
        )
        self.assertRegex(
            questionnaires_content,
            'Segundo Grupo[\s\S]+'
            'Teve alguma fratura associada à lesão?[\s\S]+'
            'Realiza Fisioterapia regularmente?[\s\S]+'
            'Faz uso de dispositivo auxiliar?[\s\S]+'
            'Qual(is)?[\s\S]+'
            'Texto mostrado ao participante'
        )

    def test_invalid_questionnaire_displays_message(self):
        ##
        # We've created invalid Questionnaire data in tests helper in first
        # experiment approved
        ##
        group = create_group(1, self.experiment)
        create_questionnaire(1, 'q4', group)
        questionnaire = Questionnaire.objects.last()
        # create invalid questionnaire language data default
        create_questionnaire_language(
            questionnaire,
            settings.BASE_DIR + '/experiments/tests/questionnaire4.csv',
            'en'
        )

        # The new visitor is at home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # As there's a questionnaire from a group that has the wrong number
        # of columns, when the new visitor clicks in Questionnaires tab she
        # sees a message telling her that something is wrong with that
        # questionnaire.
        self.browser.find_element_by_link_text('Questionnaires').send_keys(
            Keys.ENTER
        )

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).text

        self.assertIn('The questionnaire in this language is in invalid '
                      'format, and can\'t be displayed',
                      questionnaires_content)

    def test_can_see_all_language_links_of_questionnaires_if_available(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # When the new visitor clicks in the Questionnaires tab, she sees,
        # below questionnaire titles, a sequence of buttons indicating the
        # available languages of the questionnaires
        self.browser.find_element_by_link_text('Questionnaires').click()

        ##
        # We get all the elements that contains button languages
        # and your available languages
        ##
        lang_elements = self.browser.find_elements_by_class_name(
            'language'
        )
        ##
        # As in the template the order of questionnaires varies from one
        # access to another, we join all questionnaires language codes in
        # one list to make assertions below
        ##
        q_lang_codes = ''
        for lang in lang_elements:
            q_lang_codes = q_lang_codes + ' ' + lang.text

        self.assertEqual(q_lang_codes.count('en'), 2)
        self.assertEqual(q_lang_codes.count('fr'), 1)
        self.assertEqual(q_lang_codes.count('pt-br'), 1)
        self.assertEqual(q_lang_codes.count('de'), 1)

    def test_clicking_in_pt_br_language_link_of_questionnaire_render_appropriate_language(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])
        questionnaire = Questionnaire.objects.get(code='q1')

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()
        ##
        # give some time to google chart cdn to load
        # TODO: make this better without time.sleep
        ##
        time.sleep(0.5)

        # She clicks in Questionnaires tab
        self.wait_for(
            lambda:
            self.browser.find_element_by_link_text('Questionnaires').click()
        )

        #
        # Questionnaire with code='q1' has three languages: English, French and
        # Brazilian Portuguese.
        ##
        # The visitor clicks in 'pt-br' link and the questionnaire
        # session refreshes
        self.browser.find_element_by_link_text('pt-br').click()

        ##
        # give time for ajax to complete request
        ##
        time.sleep(3)

        # When she clicks in Detail button, she can see the questionnaire
        # with questions and answers in Portugues.
        self.browser.find_element_by_xpath(
            "//a[@href='#collapse" + str(questionnaire.id) + "']"
        ).click()

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        # Sample asserts for first questionnaire, Portuguese language
        self.assertIn('História de fratura', questionnaires_content)
        self.assertIn('Já fez alguma cirurgia ortopédica?',
                      questionnaires_content)
        self.assertIn('Fez alguma cirurgia de nervo?',
                      questionnaires_content)
        self.assertIn('Identifique o evento que levou ao trauma do seu plexo '
                      'braquial. É possível marcar mais do que um evento.',
                      questionnaires_content)
        self.assertIn('Teve alguma fratura associada à lesão?',
                      questionnaires_content)
        self.assertIn('Participant answers yes or not',
                      questionnaires_content)

    def test_clicking_in_fr_language_link_of_questionnaire_render_appropriate_language(self):
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_valid_questionnaires([g1, g2])
        questionnaire = Questionnaire.objects.get(code='q1')

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + self.experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # She clicks in Questionnaires tab
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Questionnaires'
            ).send_keys(Keys.ENTER)
        )

        #
        # Questionnaire with code='q1' has three languages: English, French and
        # Brazilian Portuguese.
        ##
        # The visitor clicks in 'fr' link and the questionnaire
        # session refreshes
        self.wait_for(
            lambda: self.browser.find_element_by_link_text('fr').click()
        )

        # When she clicks in Detail button, she can see the questionnaire
        # with questions and answers in Portugues.
        self.wait_for(
            lambda: self.browser.find_element_by_xpath(
                "//a[@href='#collapse" + str(questionnaire.id) + "']"
            ).click()
        )

        ##
        # give time for ajax to complete request
        ##
        time.sleep(0.2)

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        # Sample asserts for first questionnaire, French language
        self.assertIn('Histoire de la fracture?', questionnaires_content)
        self.assertIn('Avez-vous déjà eu une chirurgie orthopédique?',
                      questionnaires_content)
        self.assertIn('Avez-vous subi une chirurgie nerveuse?',
                      questionnaires_content)
        self.assertIn('Identifiez l\'événement qui a conduit au traumatisme '
                      'de votre plexus brachial. Vous pouvez marquer plus '
                      'd\'un événement.',
                      questionnaires_content)
        self.assertIn('Avez-vous eu des fractures associées à la blessure?',
                      questionnaires_content)
        self.assertIn('Participant answers yes or not', questionnaires_content)

    def test_does_not_display_study_elements_if_they_not_exist(self):
        ##
        # create study without end_date and keywords. We won't create
        # contributors either
        ##
        create_study(1, self.experiment)

        ##
        # TODO
        # ----
        # We have to refresh live server again because in parent setUp we
        # already called it without new experiment created. When refactoring
        # tests_helper call only in the classes setUp methods.
        self.browser.get(self.browser.current_url)

        # Jucileine clicks in the experiment approved
        self.wait_for(
            lambda:
            self.browser.find_element_by_xpath(
                "//a[@href='/experiments/" + self.experiment.slug + "/']"
            ).click()
        )

        # Jucileine clicks in From study link and sees a modal with Study
        # data
        self.wait_for(
            lambda:
            self.browser.find_element_by_link_text(
                self.experiment.study.title).click()
        )

        # The modal pops up and she see the fields of the study
        self.wait_for(lambda: self.assertIn(
            self.experiment.study.title,
            self.browser.find_element_by_id('modal_study_title').text
        ))

        # As the study has no end date, no contributors and no keywords
        # those fields did not appear in study modal
        self.assertIn(
            'No end date',
            self.browser.find_element_by_id('study_enddate').text
        )
        self.assertNotIn(
            'Contributors:',
            self.browser.find_element_by_id('study_contributors').text
        )
        self.assertNotIn(
            'Keywords:',
            self.browser.find_element_by_id('keywords').text
        )

    def test_can_see_url_text_for_experiments_approved(self):

        self._access_experiment_detail_page(self.experiment)

        # TODO: see if we can get current url not just self.live_server_url
        self.wait_for(lambda: self.assertIn(
            'url: ' + self.live_server_url + '/experiments/' +
            self.experiment.slug,
            self.browser.find_element_by_class_name('detail-header').text
        ))

    def test_cannot_see_link_to_change_slug_if_user_not_in_staff(self):
        self._access_experiment_detail_page(self.experiment)
        self.wait_for_detail_page_load()

        # The user enters in experiment detail page and can't see the link
        # to change experiment slug, as only staff people can change it
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath(
                "//a[@href='#change_url_modal']"
            )

    def test_can_view_versions_tab(self):
        self.experiment.status = Experiment.APPROVED
        self.experiment.save()
        experiment_v2 = create_next_version_experiment(self.experiment)

        ##
        # have to refresh home page to display last version created above
        ##
        self.browser.refresh()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment_v2.slug) + "/']"
        ).click()

        # There's a tab written Versions
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Versions').text,
            'Versions'
        ))

    def test_does_not_display_versions_tab_if_there_are_not_versions(self):
        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(self.experiment.slug) + "/']"
        ).click()

        # As there's only one version she doesn't see the Versions tab
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_link_text('Versions')

    def test_can_view_versions_tab_content(self):
        self.experiment.status = Experiment.APPROVED
        self.experiment.save()
        experiment_v2 = create_next_version_experiment(
            self.experiment, 'Text explaining changes in version 2'
        )
        experiment_v3 = create_next_version_experiment(
            experiment_v2, 'Text explaining changes in version 3'
        )

        ##
        # have to refresh home page to display last version created above
        ##
        self.browser.refresh()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment_v3.slug) + "/']"
        ).click()

        # Rosa sees the Versions tab and click on it
        self.browser.find_element_by_link_text('Versions').click()

        # Versions tab displays the other versions of the experiment
        # excluding the current one she is in. Versions tab displays a link
        # to access specific experiment version and the text explaining what
        # was changed (the text can be in versions other than first one)
        self.wait_for(lambda: self.assertIn(
            'Version 1',
            self.browser.find_element_by_id('versions_tab').text
        ))
        versions_tab = self.browser.find_element_by_id('versions_tab').text
        self.assertIn('Other versions of this experiment', versions_tab)
        self.assertIn('Version 2', versions_tab)
        self.assertIn('Text explaining changes in version 2', versions_tab)
        self.assertNotIn('Version 3', versions_tab)

        # Ok, Rosa notes that the experiment has other two versions and she
        # can view other versions of by clicking in the links.
        # So she clicks on the first vresion
        self.browser.find_element_by_link_text('Version 1').click()

        # She sees in url address, below the experiment title, that the URL of
        # the experiment has changed to the slug of the first version
        self.wait_for(lambda: self.assertIn(
            self.experiment.slug,
            self.browser.find_element_by_id('experiment_url').text
        ))
        self.browser.find_element_by_link_text('Versions').click()

        # She clicks again in the Versions tab and notes that now there are
        # only the experiment versions 2 and 3 options to click
        self.wait_for(lambda: self.assertIn(
            'Version 2',
            self.browser.find_element_by_id('versions_tab').text
        ))
        versions_tab = self.browser.find_element_by_id('versions_tab').text
        self.assertIn('Version 3', versions_tab)
        self.assertIn('Text explaining changes in version 3', versions_tab)
        self.assertNotIn('Version 1', versions_tab)

        # Finally Rosa clicks in version 2 link to see what that version has
        self.browser.find_element_by_link_text('Version 2').click()
        self.wait_for(lambda: self.assertIn(
            experiment_v2.slug,
            self.browser.find_element_by_id('experiment_url').text
        ))


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DownloadExperimentTest(FunctionalTest):

    def setUp(self):
        create_genders()
        create_trustee_user('claudia')
        create_trustee_user('roque')
        super(DownloadExperimentTest, self).setUp()
        # license is in media/download/LICENSE.txt
        os.makedirs(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        license_file = os.path.join(TEMP_MEDIA_ROOT, 'download', 'LICENSE.txt')
        with open(license_file, 'w') as file:
            file.write('license')

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT)
        super(DownloadExperimentTest, self).tearDown()

    def access_downloads_tab_content(self, experiment):
        # Josileine wants to download the experiment data.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        # She sees that there is a "Downloads" written tab. She
        # clicks in it, and sees a section bellow the tabs with a title
        # "Select experiment data pieces to download"
        self.browser.find_element_by_link_text(
            'Downloads'
        ).send_keys(Keys.ENTER)
        downloads_tab_content = self.browser.find_element_by_id(
            'downloads_tab'
        )
        return downloads_tab_content

    def license_text_asserts(self, license_modal):
        self.assertIn(
            'Before you download, you must know this experiment is licensed '
            'under Creative Commons Attribution 4.0 '
            'International License and requires that you '
            'comply with the following:',
            license_modal.text
        )
        self.assertIn(
            'You must give appropriate credit, provide a',
            license_modal.text
        )
        self.assertIn(
            'You must give appropriate credit, provide a',
            license_modal.text
        )
        self.assertIn(
            'and indicate if changes were made. You may do so in any '
            'reasonable manner, but not in any way that suggests the '
            'licensor endorses you or your use.',
            license_modal.text
        )

    def test_can_see_link_to_download_all_experiment_data_at_once(self):
        self.access_downloads_tab_content(self.experiment)

        # In right side of the Download tab content, she sees a button
        # to download all data at once
        button_download = self.browser.find_element_by_id(
            'button_download')
        self.assertEqual(
            'Download all experiment data',
            button_download.text
        )

    def test_can_see_section_content_of_downloads_tab(self):
        create_study(1, self.experiment)
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_experimental_protocol(g2)
        g3 = create_group(1, self.experiment)
        create_experimental_protocol(g3)
        q1 = create_questionnaire(1, 'q_test', g3)
        create_questionnaire_language(
            q1,
            settings.BASE_DIR + '/experiments/tests/questionnaire1_pt-br.csv',
            'pt-br'
        )
        g4 = create_group(1, self.experiment)
        p1 = create_participant(1, g4, Gender.objects.first())
        p2 = create_participant(1, g4, Gender.objects.last())
        eeg_step = create_step(1, g4, Step.EEG)
        eeg_setting = create_eeg_setting(1, self.experiment)
        create_eeg_data(eeg_setting, eeg_step, p2)

        # Josileine acessa a aba Downloads
        downloads_tab_content = self.access_downloads_tab_content(
            self.experiment
        )
        ##
        # wait for tree-multiselect plugin to render multiselection
        ##
        time.sleep(0.5)

        # She sees a tree with selections to run download
        self.wait_for(
            lambda:
            self.assertEqual(
                'Select experiment data itens to download',
                downloads_tab_content.find_element_by_tag_name('h4').text
            )
        )

        # Group g1 have neither experimental protocol nor at least
        # one participant so for Group g1, Josileine sees a message that
        # this group has no data
        self.assertIn(
            'There are not data for group ' + g1.title,
            downloads_tab_content.text
        )

        # Groups g2, g3, and g4 have at experimental protocol,
        # or participant, so Josileine see selections for that groups
        for group in [g2, g3, g4]:
            self.assertIn(
                'Group ' + group.title, downloads_tab_content.text
            )

        # Group g2 and g3 have experimental protocol, so Josileine sees a
        # selection for experimental protocol data in that two groups
        self.assertEqual(
            2, downloads_tab_content.text.count('Experimental Protocol Data')
        )

        # Group g3 has questionnaire, so Josileine see one entry selection
        # to that group about questionnaire data
        self.assertIn('Per Questionnaire Data', downloads_tab_content.text)

        # Group g4 has two participants, one with data collection and other
        # without data collection, so Josileine sees an entry for one
        # participant and doesn't see an entry for the other participant
        self.assertNotIn(
            'Participant ' + str(p1.code), downloads_tab_content.text
        )
        self.assertIn(
            'Participant ' + str(p2.code), downloads_tab_content.text
        )

    def test_can_see_groups_data_in_downloads_tab_content_only_if_there_are_groups(self):
        ##
        # Experiment has not data besides strict experiment data
        ##
        downloads_tab_content = self.access_downloads_tab_content(
            self.experiment
        )

        # Now, as there're no data for groups, she sees a message telling
        # her that there is only basic experiment data available to download
        self.assertIn(
            'There are not experiment groups data for this experiment. Click '
            'in "Download" button to download basic experiment data',
            downloads_tab_content.text
        )
        self.assertNotIn('Groups', downloads_tab_content.text)
        self.assertNotIn(
            'Experimental Protocol Data', downloads_tab_content.text
        )
        self.assertNotIn(
            'Per Participant Data', downloads_tab_content.text
        )
        self.assertNotIn('Per Questionnaire data', downloads_tab_content.text)
        self.assertNotIn('Participant ', downloads_tab_content.text)

    def test_can_see_groups_items_in_downloads_tab_content_only_if_they_exist(self):
        ##
        # Simulate that Portal received an experiment, only with
        # Experiment and Group data. One group created has no data besides
        # Group data, the other has 1 participant associated
        ##
        # create_genders()  # when eliminating global_ft() return with
        g1 = create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_participant(1, g2, Gender.objects.last())

        ##
        # We have to refresh page to include this new experiment in
        # Experiments List
        ##
        self.browser.refresh()

        downloads_tab_content = self.access_downloads_tab_content(
            self.experiment
        )

        # As the last group created has only basic participant information (
        # without data collection for it), that group is not listed.
        self.assertNotIn(
            'Group ' + self.experiment.groups.last().title,
            downloads_tab_content.text
        )
        self.assertIn(
            'There are not data for group ' +
            g1.title +
            ". But there's still basic Experiment data. Click in 'Download' "
            "button to download it.",
            downloads_tab_content.text
        )
        self.assertNotIn('Per Questionnaire Data', downloads_tab_content.text)

        # Obs.: the tests for having one of experimental protocol,
        # participants, and questionnaires, for all groups are not beeing made
        # because they are been tested indirectly by negation in this test

    def test_can_see_download_experiment_data_form_submit_button(self):
        self.access_downloads_tab_content(self.experiment)

        # Josileine sees the button to download experiment data options that
        # she's just selected.
        button = self.browser.find_element_by_id('download_button')
        self.assertEqual('Download', button.get_attribute('value'))

    def test_clicking_in_download_all_experiment_data_without_compressed_file_returns_error_message(self):
        ##
        # create temporary experiment download subdir
        ##
        os.makedirs(
            os.path.join(TEMP_MEDIA_ROOT, 'download', str(self.experiment.pk))
        )

        # Josileine accesses Experiment Detail Downloads tab
        self.access_downloads_tab_content(self.experiment)

        # wait for tree-multiselect plugin to render multiselection
        time.sleep(0.5)

        # She clicks in download all experiment data button
        self.browser.find_element_by_link_text(
            'Download all experiment data'
        ).click()

        # The modal with license warning appears and she clicks in agreement
        # button
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Agree & Download'
            ).click()
        )

        # She's redirected to experiment detail page with a message alerting
        # her that there was a problem with download (the download.zip file
        # is not in the file system)
        self.wait_for(lambda: self.assertIn(
            DOWNLOAD_ERROR_MESSAGE,
            self.browser.find_element_by_class_name('alert-danger').text
        ))

    @skip
    def test_try_to_download_without_selections_redirects_to_experiment_detail_view_with_message(self):
        ##
        # TODO:
        # This test must be ran with javascript deactivated. When we made it
        # there was not a jQuery script to prevent form submit if there's
        # not options selected to download. After we made this script.
        # So, to run this test we'd have to deactivate javascript to run it.
        # But if we deactivate javascript we can't even click in Downloads
        # tab. So we're skipping this test by now. See
        # https://stackoverflow.com/questions/13655486/how-can-i-disable-javascript-in-firefox-with-selenium
        ##

        ##
        # create some data to download
        ##
        create_study(1, self.experiment)
        create_group(1, self.experiment)
        g2 = create_group(1, self.experiment)
        create_experimental_protocol(g2)
        g3 = create_group(1, self.experiment)
        create_experimental_protocol(g3)

        self.access_downloads_tab_content(self.experiment)

        # Josileine goes directly to Download button and click on it.
        self.browser.find_element_by_id('download_button').click()

        # As she's not selected any item to download, she's redirected to
        # experiment detail page with a message alerting her
        self.wait_for(lambda: self.assertIn(
            'Please select item(s) to download',
            self.browser.find_element_by_class_name('alert-warning').text
        ))

    def test_if_there_is_not_a_subdir_in_download_dir_structure_return_message(self):
        ##
        # Create stuff to build download file below
        create_study(1, self.experiment)
        g1 = create_group(1, self.experiment)
        root_step1 = create_step(1, g1, Step.BLOCK)
        exp_prot1 = create_experimental_protocol(g1)
        exp_prot1.root_step = root_step1
        exp_prot1.save()
        p1 = create_participant(1, g1, Gender.objects.get(name='male'))
        q1 = create_questionnaire(1, 'Q5489', g1)
        create_questionnaire_language(
            q1, settings.BASE_DIR + '/experiments/tests/questionnaire7.csv',
            'en'
        )
        create_questionnaire_responses(
            q1, p1,
            settings.BASE_DIR +
            '/experiments/tests/response_questionnaire7.json'
        )
        q1.parent = root_step1
        q1.save()
        q2 = create_questionnaire(1, 'Q5345', g1)
        create_questionnaire_language(
            q2, settings.BASE_DIR + '/experiments/tests/questionnaire7.csv',
            'en'
        )
        create_questionnaire_responses(
            q2, p1,
            settings.BASE_DIR +
            '/experiments/tests/response_questionnaire7.json'
        )
        q2.parent = root_step1
        q2.save()

        download_create(self.experiment.id, '')

        # Josileine accesses Experiment Detail Downloads tab
        self.access_downloads_tab_content(self.experiment)
        # wait for tree-multiselect plugin to render multiselection
        time.sleep(0.5)  # TODO: implicit wait. Fix this!

        options = [
            'experimental_protocol_g' + str(g1.id),
            'questionnaires_g' + str(g1.id),
            'participant_p' + str(p1.id) + '_g' + str(g1.id)
        ]
        selected = choice(options)

        ##
        # Remove the subdir correspondent to the option she selected to
        # simulate that subdir was not created when creating the download dir
        # structure after experiment is ready to be analysed.
        ##
        remove_selected_subdir(
            selected, self.experiment, p1, g1, TEMP_MEDIA_ROOT
        )

        # She selects one option to download and click in Download button
        self.wait_for(
            lambda: self.browser.find_element_by_xpath(
                "//div[@data-value='" + selected + "']"
            ).find_element_by_tag_name('input').click()
        )

        self.browser.find_element_by_id('download_button').click()

        # The modal with license warning appears and she clicks in agreement
        # button
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Agree & Download'
            ).click()
        )

        # She sees an error message telling her that some problem ocurred
        self.wait_for(lambda: self.assertIn(
            DOWNLOAD_ERROR_MESSAGE,
            self.browser.find_element_by_class_name('alert-danger').text
        ))

    def test_clicking_in_download_all_experiment_data_link_pops_up_a_modal_with_license_warning_1(self):
        ##
        # Test when there are experiment researchers
        ##
        study = create_study(1, self.experiment)
        create_researcher(study, 'Renan', 'da Silva')
        create_experiment_researcher(self.experiment, 'Anibal', 'das Dores')
        create_experiment_researcher(self.experiment, 'Joseph', 'Hildegard')
        create_experiment_researcher(self.experiment, 'Antônio', 'Farias')

        self.access_downloads_tab_content(self.experiment)

        # After access Download tab in Experiment detail page, she clicks in
        # Download all experiment data link
        self.browser.find_element_by_id('button_download').click()
        time.sleep(0.5)  # necessary to wait for modal content to load

        # She sees a modal warning her from License of the data that will
        # be downloaded
        license_modal = \
            self.wait_for(
                lambda:
                self.browser.find_element_by_id('license_modal')
            )

        self.license_text_asserts(license_modal)

        # In the modal there is also how to cite that experiment in her own
        # work
        self.assertIn('How to cite this experiment:', license_modal.text)
        self.assertIn(
            'das Dores'.upper() + ', Anibal', license_modal.text
        )
        self.assertIn(
            'Hildegard'.upper() + ', Joseph', license_modal.text
        )
        self.assertIn(
            'Farias'.upper() + ', Antônio', license_modal.text
        )
        self.assertIn(
            self.experiment.title + '. Sent date: ' + str(
                self.experiment.sent_date.strftime('%B %d, %Y')),
            license_modal.text
        )
        self.assertNotIn(
            self.experiment.study.researcher.last_name.upper() + ', ' +
            self.experiment.study.researcher.first_name,
            license_modal.text
        )

    def test_clicking_in_download_all_experiment_data_link_pops_up_a_modal_with_license_warning_2(self):
        ##
        # Test when there is no experiment researchers, only the study
        # researcher
        ##
        study = create_study(1, self.experiment)
        create_researcher(study, 'Renan', 'da Silva')

        self.access_downloads_tab_content(self.experiment)

        # After access Download tab in Experiment detail page, she clicks in
        # Download all experiment data link
        self.browser.find_element_by_id('button_download').click()
        time.sleep(0.5)  # necessary to wait for modal content to load

        # She sees a modal warning her from License of the data that will
        # be downloaded
        license_modal = \
            self.wait_for(
                lambda:
                self.browser.find_element_by_id('license_modal')
            )

        self.license_text_asserts(license_modal)

        # In the modal there is also how to cite that experiment in her own
        # work
        self.assertIn('How to cite this experiment:', license_modal.text)
        self.assertIn(
            self.experiment.study.researcher.last_name.upper() + ', ' +
            self.experiment.study.researcher.first_name,
            license_modal.text
        )
        self.assertIn(
            self.experiment.title + '. Sent date: ' +
            self.experiment.sent_date.strftime('%B %d, %Y') + '.',
            license_modal.text
        )

    def test_clicking_in_download_button_pops_up_a_modal_with_license_warning(self):
        group = create_group(1, self.experiment)
        create_experimental_protocol(group)
        self.access_downloads_tab_content(self.experiment)

        # Josileine selects an item to download and clicks in download button
        self.wait_for(
            lambda: self.browser.find_element_by_xpath(
                "//input[@type='checkbox']"
            ).click()
        )
        self.browser.find_element_by_id('download_button').click()
        time.sleep(0.5)  # necessary to wait for modal content to load

        # She sees a modal warning her from License of the data that will
        # be downloaded
        license_modal = \
            self.wait_for(
                lambda:
                self.browser.find_element_by_id('license_modal')
            )

        self.license_text_asserts(license_modal)

    def test_how_to_cite_in_license_modal_is_equal_to_how_to_cite_in_citation_file_1(self):
        create_study(1, self.experiment)
        create_researcher(self.experiment.study, 'Valdick', 'Soriano')
        download_create(self.experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(self.experiment.id),
            'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')

        # Joseleine access the download tab of the last approved experiment
        self.access_downloads_tab_content(self.experiment)

        # After access Download tab in Experiment detail page, she clicks in
        # Download all experiment data link
        self.browser.find_element_by_id('button_download').click()
        time.sleep(0.5)  # necessary to wait for modal content to load

        # She sees a modal warning her from License of the data that will
        # be downloaded
        license_modal = \
            self.wait_for(
                lambda:
                self.browser.find_element_by_id('license_modal')
            )

        # She has downloaded the experiment once and wants to see if the
        # "How to cite" in license modal is equal to the "How to cite" in
        # CITATION.txt file
        self.assertIn(
            'SORIANO, Valdick. ' + self.experiment.title + '. Sent date: '
            + str(self.experiment.sent_date),
            file.read().decode('utf-8')
        )
        self.assertIn(
            'SORIANO, Valdick. ' + self.experiment.title
            + '. Sent date: '
            + self.experiment.sent_date.strftime('%B %d, %Y'),
            license_modal.text
        )

    def test_how_to_cite_in_license_modal_is_equal_to_how_to_cite_in_citation_file_2(self):
        create_study(1, self.experiment)
        create_researcher(self.experiment.study, 'Valdick', 'Soriano')
        researcher1 = create_experiment_researcher(self.experiment, 'Diana', 'Ross')
        researcher1.citation_order = 21
        researcher1.citation_name = 'ROSS B., Diana'
        researcher1.save()
        create_experiment_researcher(
            self.experiment, 'Guilherme', 'Boulos'
        )
        researcher3 = create_experiment_researcher(
            self.experiment, 'Edimilson', 'Costa'
        )
        researcher3.citation_order = 3
        researcher3.save()
        download_create(self.experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(self.experiment.id),
            'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')

        # Joseleine access the download tab of the last approved experiment
        self.access_downloads_tab_content(self.experiment)

        # After access Download tab in Experiment detail page, she clicks in
        # Download all experiment data link
        self.browser.find_element_by_id('button_download').click()
        time.sleep(0.5)  # necessary to wait for modal content to load

        # She sees a modal warning her from License of the data that will
        # be downloaded
        license_modal = \
            self.wait_for(
                lambda:
                self.browser.find_element_by_id('license_modal')
            )

        # She has downloaded the experiment once and wants to see if the
        # "How to cite" in license modal is equal to the "How to cite" in
        # CITATION.txt file
        self.assertIn(
            'COSTA, Edimilson; ROSS B., Diana; BOULOS, Guilherme. ' +
            self.experiment.title + '. Sent date: ' +
            str(self.experiment.sent_date),
            file.read().decode('utf-8')
        )
        self.assertIn(
            'COSTA, Edimilson; ROSS B., Diana; BOULOS, Guilherme. '
            + self.experiment.title + '. Sent date: '
            + self.experiment.sent_date.strftime('%B %d, %Y'),
            license_modal.text
        )

