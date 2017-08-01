from datetime import datetime
from random import randint, choice

from django.contrib.auth import models
from faker import Factory

from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, Participant, Gender, ExperimentalProtocol, \
    ClassificationOfDiseases, Keyword


def create_experiment_groups(qtty, experiment):
    """
    :param qtty: Number of groups
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    for i in range(qtty):
        Group.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=150),
            experiment=experiment
        )


def create_study(experiment):
    """
    :param experiment: Experiment to be associated with Study
    """
    fake = Factory.create()

    Study.objects.create(
        title=fake.text(max_nb_chars=15),
        description=fake.text(max_nb_chars=200),
        start_date=datetime.utcnow(), experiment=experiment
    )


def create_experiment(qtty, owner, status):
    """
    :param qtty: Number of experiments
    :param owner: Owner of experiment - User instance model
    :param status: Expeeriment status
    """
    fake = Factory.create()

    for i in range(qtty):
        experiment = Experiment.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            nes_id=randint(1, 10000),  # TODO: guarantee that this won't
            # genetates constraint violaton (nes_id, owner_id)
            owner=owner, version=1,
            sent_date=datetime.utcnow(),
            status=status,
            data_acquisition_done=choice([True, False])
        )
        create_study(experiment)
        create_experiment_groups(randint(2, 3), experiment)


def create_trustee_users():
    group = models.Group.objects.create(name='trustees')

    # Create 2 trustee users and add them to trustees group
    trustee1 = models.User.objects.create_user(
        username='claudia', first_name='Claudia', last_name='Vargas',
        password='passwd'
    )
    trustee2 = models.User.objects.create_user(
        username='roque', first_name='Antonio', last_name='Roque',
        password='passwd'
    )
    group.user_set.add(trustee1)
    group.user_set.add(trustee2)


def create_researchers():
    fake = Factory.create()

    for study in Study.objects.all():
        Researcher.objects.create(
            name=fake.name(),
            email=fake.email(),
            study=study
        )
        Collaborator.objects.create(name=fake.text(max_nb_chars=15),
                                    team=fake.text(max_nb_chars=15),
                                    coordinator=False, study=study)


def create_participants(qtty, group, gender):
    """
    :param gender:
    :param qtty:
    :param group: Group model instance
    """
    code = randint(1, 1000)
    for j in range(qtty):
        Participant.objects.create(
            code=code, age=randint(18, 80),
            gender=gender,
            group=group
        )
        code += 1


def create_experiment_protocol(group):
    """
    :type group: Group model instance
    """
    fake = Factory.create()

    ExperimentalProtocol.objects.create(
        group=group,
        textual_description=fake.text()
    )
    for exp_pro in ExperimentalProtocol.objects.all():
        image_file = generate_image_file(
            randint(100, 800), randint(300, 700), fake.word() + '.jpg'
        )
        exp_pro.image.save(image_file.name, image_file)
        exp_pro.save()
        # Update image of last experimental protocol with a null image to test
        # displaying default image: "No image"
    exp_pro = ExperimentalProtocol.objects.last()
    exp_pro.image = None
    exp_pro.save()


def create_classification_of_deseases(qtty):
    """
    :param qtty: number of objects to create 
    """
    fake = Factory.create()

    for i in range(qtty):
        ClassificationOfDiseases.objects.create(
            code=randint(1, 1000), description=fake.text(),
            abbreviated_description=fake.text(max_nb_chars=100),
            parent=None
        )


def create_study_collaborator(qtty, study):
    """
    :param qtty: number of collaborators 
    :param study: Study model instance
    """
    fake = Factory.create()

    for i in range(qtty):
        Collaborator.objects.create(
            name=fake.name(), team=fake.word(),
            coordinator=randint(0, 1),
            study=study
        )


def create_keyword(qtty):
    """
    :param qtty: number of keywords to be created 
    """
    fake = Factory.create()

    Keyword.objects.create(name=fake.word())
    for i in range(qtty):
        while True:
            keyword = fake.word()
            if not Keyword.objects.filter(name=keyword):
                break
        Keyword.objects.create(name=keyword)


def associate_experiments_to_trustees():
    trustee1 = models.User.objects.get(username='claudia')  # requires
    # creates trustee Claudia
    trustee2 = models.User.objects.get(username='roque')  # requires
    # creates trustee Roque
    for experiment in Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS):
        experiment.trustee = choice([trustee1, trustee2])
    # Guarantee that at least one experiment has trustee as Claudia and one
    # experiment has trustee as Roque (requires creates at least two
    # experiments that are under analysis).
    exp1 = Experiment.objects.filter(status=Experiment.UNDER_ANALYSIS).first()
    exp2 = Experiment.objects.filter(status=Experiment.UNDER_ANALYSIS).last()
    exp1.trustee = trustee1
    exp1.save()
    exp2.trustee = trustee2
    exp2.save()


def create_ethics_committee_info(experiment):
    fake = Factory.create()

    experiment.project_url = fake.uri()
    experiment.ethics_committee_url = fake.uri()
    # TODO: generate PDF
    file = generate_image_file(500, 800, fake.word() + '.jpg')
    experiment.ethics_committee_file.save(file.name, file)
    experiment.save()


def global_setup_ft():
    """
    This global setup creates basic object models that are used in 
    functional tests.
    """
    # Create 2 API clients
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    # Create group Trustees
    create_trustee_users()

    # Create 5 experiments for 2 owners, randomly, and studies (groups are
    # created inside create_experiment_and_study)
    create_experiment(2, choice([owner1, owner2]),
                      Experiment.TO_BE_ANALYSED)
    # TODO: when creating experiment UNDER_ANALYSIS, associate with a trustee
    create_experiment(2, choice([owner1, owner2]),
                      Experiment.UNDER_ANALYSIS)
    create_experiment(4, choice([owner1, owner2]),
                      Experiment.APPROVED)
    # Put some non-random strings in two approved experiments to test search
    experiment = Experiment.objects.last()
    experiment.title = 'Brachial Plexus'
    experiment.save()
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    # We change first experiment study approved to contain 'brachial' in
    # study description, so it have to be found by search test
    study = Study.objects.filter(
        experiment__status=Experiment.APPROVED
    ).first()
    study.description = 'The brachial artery is the major blood vessel of ' \
                        'the (upper) arm. It\'s correlated with plexus.'
    study.save()
    # We change experiment description to test search
    experiment = Experiment.objects.last()
    experiment.description = 'Brachial plexus repair by peripheral nerve ' \
                             'grafts directly into the spinal cord in rats ' \
                             'Behavioral and anatomical evidence of ' \
                             'functional recovery'
    experiment.save()
    # To test search
    group = Group.objects.first()
    group.description = 'Plexus brachial is writed in wrong order. Correct ' \
                        'is Brachial plexus.'
    group.save()

    # We create one experiment approved with ethics committee information
    create_ethics_committee_info(Experiment.objects.last())
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.NOT_APPROVED)

    # Associate trustee to studies under analysis (requires create
    # experiments before)
    associate_experiments_to_trustees()

    # Create study collaborators (requires creating studies before)
    for study in Study.objects.all():
        create_study_collaborator(randint(2, 3), study)

    # Create some keywords to associate with studies
    create_keyword(10)
    # Associate keywords with studies
    for study in Study.objects.all():
        kw1 = choice(Keyword.objects.all())
        kw2 = choice(Keyword.objects.all())
        kw3 = choice(Keyword.objects.all())
        study.keywords.add(kw1, kw2, kw3)

    # Create genders
    gender1 = Gender.objects.create(name='male')
    gender2 = Gender.objects.create(name='female')

    # Create some entries for ClassificationOfDiseases
    create_classification_of_deseases(10)

    # Create randint(3, 7) participants for each group (requires create
    # groups before)
    for group in Group.objects.all():
        create_experiment_protocol(group)
        create_participants(
            randint(3, 7), group,
            gender1 if randint(1, 2) == 1 else gender2
        )
        ic1 = choice(ClassificationOfDiseases.objects.all())
        ic2 = choice(ClassificationOfDiseases.objects.all())
        group.inclusion_criteria.add(ic1, ic2)

    # Create researchers associated to studies created in
    # create_experiment_and_study method
    # Requires running create_experiment_study_group before
    create_researchers()


def global_setup_ft_search():
    pass


def global_setup_ut():
    """
    This global setup creates basic object models that are used in 
    unittests.
    """
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    # Create group Trustees
    create_trustee_users()

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.UNDER_ANALYSIS,
        trustee=models.User.objects.get(username='claudia')
    )
    experiment3 = Experiment.objects.create(
        title='Experiment 3', nes_id=2, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    create_ethics_committee_info(experiment3)

    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    study2 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment2)
    # Create a study and doesn't associate it with researcher bellow.
    # This is to testing creating research associate it with a study in
    # test_models.py
    Study.objects.create(start_date=datetime.utcnow(),
                         experiment=experiment3)

    Researcher.objects.create(name='Raimundo Nonato',
                              email='rnonato@example.com', study=study1)
    Researcher.objects.create(name='Raimunda da Silva',
                              email='rsilva@example.com', study=study2)

    # Create some keywords to associate with studies
    create_keyword(10)
    # Associate keywords with studies
    for study in Study.objects.all():
        kw1 = choice(Keyword.objects.all())
        kw2 = choice(Keyword.objects.all())
        kw3 = choice(Keyword.objects.all())
        study.keywords.add(kw1, kw2, kw3)

    Collaborator.objects.create(
        name='Colaborador 1', team='Numec', coordinator=True,
        study=study1
    )
    Collaborator.objects.create(
        name='Colaborador 2', team='Numec', coordinator=False,
        study=study1
    )


def apply_setup(setup_func):
    """
    Defines a decorator that uses global setup method.
    :param setup_func: global setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap
