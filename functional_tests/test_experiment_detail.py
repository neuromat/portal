import os
import tempfile
import time
from random import choice
from unittest import skip

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from downloads.views import DOWNLOAD_ERROR_MESSAGE
from experiments.models import Experiment, Questionnaire, Step, Group, Gender
from experiments.tests.tests_helper import create_experiment, create_group, \
    create_participant, create_download_dir_structure_and_files, \
    remove_selected_subdir, create_experimental_protocol, \
    create_questionnaire, create_questionnaire_language, create_study, \
    create_eeg_data, create_eeg_setting, create_eeg_step, \
    create_valid_questionnaires, create_publication
from functional_tests.base import FunctionalTest
from nep import settings


class ExperimentDetailTest(FunctionalTest):

    def _access_experiment_detail_page(self, experiment):
        # The new visitor is in home page and see the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        link = self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        )
        link.click()

    # TODO: break by tabs
    def test_can_view_detail_page(self):
        # TODO: getting momentarily from tests_helper
        experiment = Experiment.objects.get(
            title='Brachial Plexus (with EMG Setting)'
        )

        self._access_experiment_detail_page(experiment)

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

        # She clicks in Related study link and sees a modal with Study data
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
        ##
        # to conform to study_start_date format in browser
        ##
        self.assertIn(experiment.study.start_date.strftime("%B %d, %Y")
                      .lstrip("0").replace(" 0", " "), study_start_date)
        # before
        # self.assertIn(experiment.study.start_date.strftime("%b. %d, %Y")
        #               .lstrip("0").replace(" 0", " "), study_start_date)
        study_end_date = self.browser.find_element_by_id(
            'study_enddate').text
        self.assertIn('End date:', study_end_date)
        if experiment.study.end_date:
            self.assertIn(experiment.study.end_date.strftime("%B %d, %Y"),
                          study_end_date)

        # Right below there is a relation of contributors of the study,
        # the contributor's team and coordinator
        study_contributors = self.browser.find_element_by_id(
            'study_contributors').text
        if experiment.study.collaborators:
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
        time.sleep(1)  # TODO: eliminate implicit wait
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

    def test_can_see_publications_link(self):
        experiment = Experiment.objects.last()
        create_publication(experiment)
        create_publication(experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment.slug) + "/']"
        ).click()

        # As last approved experiment has a publication associated with it,
        # she sees a link to publications below the experiment description
        # area, at right
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Publications').text,
            'Publications'
        ))

    def test_can_see_publications_modal_with_correct_content(self):
        experiment = Experiment.objects.last()
        create_publication(experiment)
        create_publication(experiment)
        publications = experiment.publications.all()

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment.slug) + "/']"
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
        experiment = Experiment.objects.last()
        create_publication(experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link of last approved experiment and is
        # redirected to experimentdetail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + str(experiment.slug) + "/']"
        ).click()

        # As last approved experiment has publications associated with it,
        # she sees a link to publications below the experiment description
        # area, at right. She clicks in it
        self.wait_for(lambda: self.browser.find_element_by_link_text(
            'Publications'
        ).click())

        for publication in experiment.publications.all():
            try:
                self.wait_for(
                    lambda:
                    self.browser.find_element_by_link_text(publication.url)
                )
            except NoSuchElementException:
                self.fail(publication.url + ' is not a link')

    def test_can_view_questionaire_tab(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
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
        self.wait_for_detail_page_load()

        # As there are no questionnaires for this experiment, she can't see
        # the Questionnaires tab and Questionnaires content
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_link_text('Questionnaires')

    def test_can_view_group_questionnaires_and_questionnaires_titles(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)

        ##
        # get groups objects with questionnaire steps
        ##
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = experiment.groups.filter(steps__in=q_steps)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
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
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)

        # When the new visitor visits an experiment that has questionnaires,
        # in right side of each questionnaire title is a 'Detail'
        # button. When she clicks on it, the questionnaire expand to display
        # the questions and answers.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()
        self.wait_for_detail_page_load()

        self.browser.find_element_by_link_text('Questionnaires').click()

        button_details = self.browser.find_element_by_id(
            'questionnaires_tab'
        ).find_element_by_link_text('Details')
        button_details.send_keys(Keys.ENTER)

        self.assertEqual(button_details.text, 'Details')

    def test_can_view_questionnaires_content(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)

        # The new visitor is in home page and sees the list of experiments.
        # She clicks in the "View" link corresponded to the experiment and is
        # redirected to experiment detail page.
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
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

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        ##
        # sample asserts for first questionnaire
        ##
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
        # sample asserts for second questionnaire
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
        # sample asserts for third questionnaire
        ##
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
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
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
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        questionnaire = Questionnaire.objects.get(code='q1')

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
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
        self.assertIn('The user answers yes or not',
                      questionnaires_content)

    def test_clicking_in_fr_language_link_of_questionnaire_render_appropriate_language(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        questionnaire = Questionnaire.objects.get(code='q1')

        # The visitor clicks in the experiment with questionnaire in home page
        self.browser.find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
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

        questionnaires_content = self.browser.find_element_by_id(
            'questionnaires_tab').text

        # Sample asserts for first questionnaire, Portuguese language
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
        self.assertIn('The user answers yes or not',
                      questionnaires_content)

    def test_does_not_display_study_elements_if_they_not_exist(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()
        ##
        # create study without end_date and keywords. We won't create
        # contributors either
        ##
        create_study(1, experiment)

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
                "//a[@href='/experiments/" + experiment.slug + "/']"
            ).click()
        )

        # Jucileine clicks in From study link and sees a modal with Study
        # data
        self.wait_for(
            lambda:
            self.browser.find_element_by_link_text(
                experiment.study.title).click()
        )

        # The modal pops up and she see the fields of the study
        self.wait_for(lambda: self.assertIn(
            experiment.study.title,
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

        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).first()
        self._access_experiment_detail_page(experiment)

        # TODO: see if we can get current url not just self.live_server_url
        self.wait_for(lambda: self.assertIn(
            'url: ' + self.live_server_url + '/experiments/' + experiment.slug,
            self.browser.find_element_by_class_name('detail-header').text
        ))

    def test_cannot_see_link_to_change_slug_if_user_not_in_staff(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).first()
        self._access_experiment_detail_page(experiment)
        self.wait_for_detail_page_load()

        # The user enters in experiment detail page and can't see the link
        # to change experiment slug, as only staff people can change it
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath(
                "//a[@href='#change_url_modal']"
            )


class DownloadExperimentTest(FunctionalTest):

    TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp(), 'media')

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

    def test_can_see_link_to_download_all_experiment_data_at_once(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()
        self.access_downloads_tab_content(experiment)

        # In right side of the Download tab content, she sees a button
        # to download all data at once
        button_download = self.browser.find_element_by_id(
            'button_download')
        self.assertEqual(
            'Download all experiment data',
            button_download.text
        )

    def test_can_see_section_content_of_downloads_tab(self):
        ##
        # Last approved experiment created has the objects that we need for
        # all groups, besides questionnaires and experimental protocols for
        # some groups.
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        downloads_tab_content = self.access_downloads_tab_content(experiment)
        # wait for tree-multiselect plugin to render multiselection
        time.sleep(0.5)

        self.wait_for(
            lambda:
            self.assertEqual(
                'Select experiment data itens to download',
                downloads_tab_content.find_element_by_tag_name('h4').text
            )
        )

        ##
        # Variable to count how many groups has experimental protocol that
        # will be tested below.
        ##
        experimental_protocol_counter = 0
        ##
        # Variable to count how many groups has questionnaires that
        # will be tested below.
        ##
        per_questionnaire_counter = 0
        for group in experiment.groups.all():
            ##
            # We test download selection by user, only for efective data in a
            # group. If not, test for warning message
            ##
            if not hasattr(group, 'experimental_protocol') \
                    and not group.steps.filter(
                type=Step.QUESTIONNAIRE
            ).count() > 0 and not group.participants.all():
                self.assertIn(
                    'There are not data for group ' + group.title,
                    downloads_tab_content.text
                )
            else:
                self.assertIn(
                    'Group ' + group.title, downloads_tab_content.text
                )
                if hasattr(group, 'experimental_protocol'):
                    experimental_protocol_counter += 1
                for participant in group.participants.all():
                    ##
                    # List participants only if they have data collection.
                    # Can test against downloads_tab_content because we've
                    # created different participants for each group in the
                    # tests.
                    ##
                    if participant.has_data_collection():
                        self.assertIn(
                            'Participant ' + participant.code,
                            downloads_tab_content.text
                        )
                    else:
                        self.assertNotIn(
                            'Participant ' + participant.code,
                            downloads_tab_content.text
                        )
                if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
                    per_questionnaire_counter += 1

        ##
        # test for correct number of Experimental Protocol Data options
        ##
        self.assertEqual(
            experimental_protocol_counter,
            downloads_tab_content.text.count('Experimental Protocol Data')
        )

        ##
        # test for correct number of Per Questionnaire Data options
        ##
        self.assertEqual(
            per_questionnaire_counter,
            downloads_tab_content.text.count('Per Questionnaire Data')
        )

    def test_can_see_groups_data_in_downloads_tab_content_only_if_there_are_groups(self):
        ##
        # Let's create an experiment only with Experiment data, without
        # groups data. With it, we simulate that Portal received an
        # experiment, only with Experiment data.
        ##
        owner = User.objects.get(username='lab1')
        create_experiment(1, owner, Experiment.APPROVED)
        experiment = Experiment.objects.last()

        ##
        # We have to refresh page to include this new experiment in
        # Experiments List
        ##
        self.browser.refresh()

        downloads_tab_content = self.access_downloads_tab_content(experiment)

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

    def test_can_see_groups_items_in_downloads_tab_content_only_if_they_exist(
            self):
        ##
        # Let's create an experiment with Experiment and Groups data. With
        # it, we simulate that Portal received an experiment, only with
        # Experiment and Group data. One group created has no data besides
        # Group data, the other has 1 participant associated
        ##
        owner = User.objects.get(username='lab1')
        create_experiment(1, owner, Experiment.APPROVED)
        experiment = Experiment.objects.last()
        create_group(1, experiment)
        group_with_nothing = Group.objects.last()
        create_group(1, experiment)
        create_participant(1, Group.objects.last(), Gender.objects.last())

        ##
        # We have to refresh page to include this new experiment in
        # Experiments List
        ##
        self.browser.refresh()

        downloads_tab_content = self.access_downloads_tab_content(experiment)

        # As the last group created has only basic participant information (
        # without data collection for it), that group is not listed.
        self.assertNotIn(
            'Group ' + experiment.groups.last().title,
            downloads_tab_content.text
        )
        self.assertIn(
            'There are not data for group ' +
            group_with_nothing.title +
            ". But there's still basic Experiment data. Click in 'Download' "
            "button to download it.",
            downloads_tab_content.text
        )
        self.assertNotIn('Per Questionnaire Data', downloads_tab_content.text)

        # Obs.: the tests for having one of experimental protocol,
        # participants, and questionnaires, for all groups are not beeing made
        # because they are been tested indirectly by negation in this test

    def test_can_see_download_experiment_data_form_submit_button(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).first()

        self.access_downloads_tab_content(experiment)

        # Josileine sees the button to download experiment data options that
        # she's just selected.
        button = self.browser.find_element_by_id('download_button')
        self.assertEqual('Download', button.get_attribute('value'))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_clicking_in_download_all_experiment_data_without_compressed_file_returns_error_message(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # create temporary experiment download subdir
        os.makedirs(
            os.path.join(self.TEMP_MEDIA_ROOT, 'download', str(experiment.pk))
        )

        # Josileine accesses Experiment Detail Downloads tab
        self.access_downloads_tab_content(experiment)

        # wait for tree-multiselect plugin to render multiselection
        time.sleep(0.5)

        # She clicks in download all experiment data button
        self.browser.find_element_by_link_text(
            'Download all experiment data'
        ).click()

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
        # tab. So we're skipping this test. See
        # https://stackoverflow.com/questions/13655486/how-can-i-disable-javascript-in-firefox-with-selenium
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).first()

        self.access_downloads_tab_content(experiment)

        # Josileine goes directly to Download button and click on it.
        self.browser.find_element_by_id('download_button').click()

        # As she's not selected any item to download, she's redirected to
        # experiment detail page with a message alerting her
        self.wait_for(lambda: self.assertIn(
            'Please select item(s) to download',
            self.browser.find_element_by_class_name('alert-warning').text
        ))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_if_there_is_not_a_subdir_in_download_dir_structure_return_message(self):
        # TODO: getting momentarily from tests_helper
        experiment = Experiment.objects.get(
            title='Brachial Plexus (with EMG Setting)'
        )
        for group in experiment.groups.all():
            try:
                group.experimental_protocol
            except ObjectDoesNotExist:
                create_experimental_protocol(group)
            if not group.steps.filter(type=Step.QUESTIONNAIRE):
                create_questionnaire(1, 'code', group)
                q = Questionnaire.objects.last()
                create_questionnaire_language(
                    q,
                    settings.BASE_DIR +
                    '/experiments/tests/questionnaire1.csv',
                    'en'
                )

        ##
        # Create participants data collection
        ##
        for group in experiment.groups.all():
            for participant in group.participants.all():
                eeg_setting = create_eeg_setting(1, experiment)
                eeg_step = create_eeg_step(group, eeg_setting)
                create_eeg_data(eeg_setting, eeg_step, participant)

        create_download_dir_structure_and_files(
            experiment, self.TEMP_MEDIA_ROOT
        )

        ##
        # Get the variables that we will need below
        ##
        group = experiment.groups.order_by('?').first()
        participant = group.participants.order_by('?').first()
        # there's a group that has no participants
        while True:
            if participant:
                break
            else:
                group = experiment.groups.order_by('?').first()
                participant = group.participants.order_by('?').first()

        # Josileine accesses Experiment Detail Downloads tab
        self.access_downloads_tab_content(experiment)
        # wait for tree-multiselect plugin to render multiselection
        time.sleep(0.5)  # TODO: implicit wait. Fixes this!

        options = [
            'experimental_protocol_g' + str(group.id),
            'questionnaires_g' + str(group.id),
            'participant_p' + str(participant.id) + '_g' + str(group.id)
        ]
        selected = choice(options)

        ##
        # Remove the subdir correspondent to the option she selected to
        # simulate that subdir was not created when creating the download dir
        # structure after experiment is ready to be analysed.
        ##
        remove_selected_subdir(
            selected, experiment, participant, group, self.TEMP_MEDIA_ROOT
        )

        # She selects one option to download and click in Download button
        self.wait_for(
            lambda: self.browser.find_element_by_xpath(
                "//div[@data-value='" + selected + "']"
            ).find_element_by_tag_name('input').click()
        )

        self.browser.find_element_by_id('download_button').click()

        # She sees an error message telling her that some problem ocurred
        self.wait_for(lambda: self.assertIn(
            DOWNLOAD_ERROR_MESSAGE,
            self.browser.find_element_by_class_name('alert-danger').text
        ))
