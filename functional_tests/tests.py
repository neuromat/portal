from datetime import datetime
import time

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from djipsum.faker import FakerModel
from selenium import webdriver

from experiments.models import Experiment, Study, ExperimentStatus, Group


def global_setup(self):
    """
    This setup creates basic object models that are used in tests bellow.
    :param self:
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    exp_status1 = ExperimentStatus.objects.create(tag='to_be_approved')
    exp_status2 = ExperimentStatus.objects.create(tag='approved')
    exp_status3 = ExperimentStatus.objects.create(tag='rejected')

    # Create 3 experiments for owner 1 and 2 for owner 2, and studies
    # associated
    faker = FakerModel(app='experiments', model='Experiment')

    for i in range(0, 3):
        experiment_owner1 = Experiment.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i+1,
            owner=owner1, version=1, status=exp_status2,
            sent_date=datetime.utcnow()
        )
        Study.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i+1, start_date=datetime.utcnow(),
            experiment=experiment_owner1, owner=owner1
        )
        Group.objects.create(
            nes_id=i+1, title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment_owner1, owner=owner1
        )

    for i in range(3, 5):
        experiment_owner2 = Experiment.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i + 1,
            owner=owner2, version=1, status=exp_status2,
            sent_date=datetime.utcnow()
        )
        Study.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i + 1, start_date=datetime.utcnow(),
            experiment=experiment_owner2, owner=owner1
        )
        Group.objects.create(
            nes_id=i+1, title=faker.fake.text(max_nb_chars=50),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment_owner2, owner=owner2
        )


def apply_setup(setup_func):
    """
    Defines a decorator that uses my_setup method.
    :param setup_func: my_setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap


@apply_setup(global_setup)
class NewVisitorTest(StaticLiveServerTestCase):

    def setUp(self):
        global_setup(self)
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_view_initial_page(self):
        # A neuroscience researcher discovered a new site that
        # provides a data base with neuroscience experiments.
        # She goes to checkout its home page
        self.browser.get(self.live_server_url)

        # She notices the page title and header mention
        # Neuroscience Experiments Database
        self.assertIn('Neuroscience Experiments Database', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Neuroscience Experiments Database', header_text)

        # She sees that in header bunner there is a search box invited her
        # to type terms/words that will be searched in the portal
        searchbox = self.browser.find_element_by_id('id_search_box')
        self.assertEqual(
            searchbox.get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )

        # As there are experiments sended to Portal, she sees the home
        # page have a list of experiments in a table.
        # She reads in "List of Experiments" in the table title
        table_title = self.browser.find_element_by_id(
            'id_table_title').find_element_by_tag_name('h2').text
        self.assertEqual('List of Experiments', table_title)

        # She sees a list of experiments with columns: Title, Description
        table = self.browser.find_element_by_id('id_experiments_table')
        row_headers = table.find_element_by_tag_name(
            'thead').find_element_by_tag_name('tr')
        col_headers = row_headers.find_elements_by_tag_name('th')
        self.assertTrue(col_headers[0].text == 'Title')
        self.assertTrue(col_headers[1].text == 'Description')
        self.assertTrue(col_headers[2].text == 'Groups')
        self.assertTrue(col_headers[3].text == 'Version')

        # She sees the content of the list
        experiment = Experiment.objects.first()
        rows = table.find_element_by_tag_name('tbody')\
            .find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                experiment.title for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[1].text ==
                experiment.description for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[2].text ==
                str(experiment.groups.count()) for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[3].text ==
                str(experiment.version) for row in rows)
        )

        # She notices that in the footer there is information
        # about ways of contact institution.
        footer_contact = self.browser.find_element_by_id('id_footer_contact')
        footer_header_text = footer_contact.find_element_by_tag_name('h4').text
        self.assertIn('Contact', footer_header_text)
        footer_content = footer_contact.find_element_by_id(
            'id_footer_contact').text
        self.assertIn('Address:', footer_content)
        self.assertIn('Matão St., 1010 - Cidade Universitária - São Paulo - '
                      'SP - Brasil. 05508-090. Veja o mapa', footer_content)
        self.assertIn('Phone:', footer_content)
        self.assertIn('+55 11 3091-1717', footer_content)
        self.assertIn('Email:', footer_content)
        self.assertIn('neuromat@numec.prp.usp.br', footer_content)
        self.assertIn('Media contact:', footer_content)
        self.assertIn('comunicacao@numec.prp.usp.br', footer_content)
        footer_license_text = self.browser.find_element_by_id(
            'id_footer_license').text
        self.assertIn('This site content is licensed with Creative Commons '
                      'Attributions 3.0', footer_license_text)

        # She notices "View" link, in last column
        table = self.browser.find_element_by_id('id_experiments_table')
        rows = table.find_element_by_tag_name('tbody')\
            .find_elements_by_tag_name('tr')
        self.assertTrue(
            all(row.find_elements_by_tag_name('td')[4].text ==
                'View' for row in rows)
        )

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
        study_title = self.browser.find_element_by_id('modal_study_title').text
        self.assertIn(experiment.study.title, study_title)
        study_description = self.browser.find_element_by_id(
            'modal_study_description').text
        self.assertIn(experiment.study.description, study_description)
        study_researcher = self.browser.find_element_by_id(
            'modal_study_researcher').text
        self.assertIn('Researcher:', study_researcher)
        study_start_date = self.browser.find_element_by_id(
            'modal_study_startdate').text
        self.assertIn('Start date:', study_start_date)
        self.assertIn(experiment.study.start_date.strftime("%B %d, %Y"),
                      study_start_date)
        study_end_date = self.browser.find_element_by_id(
            'modal_study_enddate').text
        self.assertIn('End date:', study_end_date)
        if experiment.study.end_date:
            self.assertIn(experiment.study.end_date.strftime("%B %d, %Y"),
                          study_end_date)
        else:
            self.assertIn(str(None), study_end_date)
        study_contributors = self.browser.find_element_by_id(
            'modal_contributors').text
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

        self.fail('Finish the test!')
