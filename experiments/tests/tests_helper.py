from datetime import datetime
from random import randint, choice

from django.contrib.auth import models
from faker import Factory

from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, Participant, Gender, ExperimentalProtocol


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


def create_experiment_and_study(qtty, owner, status):
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
            status=status
        )
        Study.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            start_date=datetime.utcnow(), experiment=experiment
        )
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
            name=fake.text(max_nb_chars=15),
            email=fake.text(max_nb_chars=15),
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
    fake = Factory.create()

    for j in range(qtty):
        Participant.objects.create(
            code=fake.ssn(), age=randint(18, 80),
            gender=gender,
            group=group
        )


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
            randint(100, 500), randint(300, 700), fake.word() + '.jpg')
        exp_pro.image.save(image_file.name, image_file)
        exp_pro.save()
        # Update image of last experimental protocol with a null image to test
        # displaying default image: "No image"
    exp_pro = ExperimentalProtocol.objects.last()
    exp_pro.image = None
    exp_pro.save()


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

    # Create 3 experiments for owner 1 and 2 for owner 2, and studies,
    # and groups associated
    create_experiment_and_study(2, choice([owner1, owner2]), Experiment.TO_BE_ANALYSED)
    create_experiment_and_study(1, choice([owner1, owner2]), Experiment.UNDER_ANALYSIS)
    create_experiment_and_study(1, choice([owner1, owner2]), Experiment.APPROVED)
    create_experiment_and_study(1, choice([owner1, owner2]), Experiment.NOT_APPROVED)

    # create genders
    gender1 = Gender.objects.create(name='male')
    gender2 = Gender.objects.create(name='female')

    # Create randint(3, 7) participants for each group (requires create
    # groups before)
    for group in Group.objects.all():
        create_experiment_protocol(group)
        create_participants(
            randint(3, 7), group,
            gender1 if randint(1, 2) == 1 else gender2)

    # Create researchers associated to studies created in
    # create_experiment_and_study method
    # Requires running create_experiment_study_group before
    create_researchers()


def global_setup_ut():
    """
    This global setup creates basic object models that are used in 
    unittests.
    """
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.UNDER_ANALYSIS
    )

    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    Study.objects.create(start_date=datetime.utcnow(),
                         experiment=experiment2)

    Researcher.objects.create(name='Raimundo Nonato',
                              email='rnonato@example.com', study=study1)
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
