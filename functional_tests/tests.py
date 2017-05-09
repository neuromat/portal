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
            owner=owner, study=study
        )

    return Experiment.objects.all()


class NewVisitorTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        # We post some experiments to test list experiments to the new visitor.
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        create_experiments(3, owner)

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
            'Type key terms/words to be searhed'
        )

        # She sees the home page have a list of experiments
        table = self.browser.find_element_by_id('id_experiments_table')

        self.fail('Finish the test!')
