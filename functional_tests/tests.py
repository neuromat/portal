from datetime import datetime
from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from loremipsum import get_sentences, get_paragraphs
from selenium import webdriver

from experiments.models import Experiment, Study, Researcher


def create_researcher(quantity, owner):
    first_names = get_sentences(quantity)

    for i in range(0, quantity):
        Researcher.objects.create(first_name=first_names[i], nes_id=i+1,
                                  owner=owner)

    return Researcher.objects.all()


def create_studies(quantity, owner):
    researcher = create_researcher(1, owner).first()
    titles = get_sentences(quantity)
    descriptions = get_paragraphs(quantity)

    for i in range(0, quantity):
        Study.objects.create(
            title=titles[i], description=descriptions[i],
            start_date=datetime.utcnow(), nes_id=i+1, researcher=researcher,
            owner=owner
        )

    return Study.objects.all()


def create_experiments(quantity, owner):
    study = create_studies(1, owner).first()
    titles = get_sentences(quantity)
    descriptions = get_paragraphs(quantity)

    for i in range(0, quantity):
        Experiment.objects.create(
            title=titles[i], description=descriptions[i], nes_id=i+1,
            owner=owner, study=study, version=1
        )

    return Experiment.objects.all()


class NewVisitorTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_view_initial_page(self):
        # We post some experiments to test list experiments to the new visitor.
        # TODO: test for no experiments approved
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        create_experiments(3, owner)

        # A neuroscience researcher discovered a new site that
        # provides a data base with neuroscience experiments.
        # She goes to checkout its home page
        self.browser.get(self.live_server_url)

        # She notices the page title and header mention
        # Neuroscience Experiments Database
        self.assertIn('Neuroscience Experiments Database', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Neuroscience Experiments Database', header_text)

        ##
        # Tests for header
        ##
        # She sees that in header bunner there is a search box invited her
        # to type terms/words that will be searched in the portal
        searchbox = self.browser.find_element_by_id('id_search_box')
        self.assertEqual(
            searchbox.get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )

        ##
        # Tests for content
        ##
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
        # She sees the content of the list
        experiment = Experiment.objects.first()
        rows = table.find_element_by_tag_name(
            'tbody').find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[0].text ==
                experiment.title for row in rows)
        )
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[1].text ==
                experiment.description for row in rows)
        )

        ##
        # Tests for footer
        ##
        # She notices that in the footer there is information
        # about ways of contact institution.
        footer_section = self.browser.find_element_by_id('id_footer_section')
        footer_header_text = footer_section.find_element_by_tag_name('h4').text
        self.assertIn('Contact', footer_header_text)
        footer_content = footer_section.find_element_by_id(
            'id_footer_content').text
        self.assertIn('Address:', footer_content)
        self.assertIn('Matão St., 1010 - Cidade Universitária - São Paulo - '
                      'SP - Brasil. 05508-090. Veja o mapa', footer_content)
        self.assertIn('Phone:', footer_content)
        self.assertIn('+55 11 3091-1717', footer_content)
        self.assertIn('Email:', footer_content)
        self.assertIn('neuromat@numec.prp.usp.br', footer_content)
        self.assertIn('Media contact:', footer_content)
        self.assertIn('comunicacao@numec.prp.usp.br', footer_content)
        footer_license = footer_section.find_element_by_id('id_license').text
        self.assertIn('This site content is licensed with Creative Commons '
                      'Attributions 3.0.', footer_license)

        self.fail('Finish the test!')


