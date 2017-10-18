from modeltranslation.translator import TranslationOptions, translator

from experiments.models import ClassificationOfDiseases, Gender


class ClassificationOfDiseasesTranslationOptions(TranslationOptions):
    fields = ('description', 'abbreviated_description')


translator.register(
    ClassificationOfDiseases, ClassificationOfDiseasesTranslationOptions
)


# TODO: this is not working. The migrations passes, but in views can't get
# TODO: the pt-BR translation. Gets error: "Matching query does not exist" for
# TODO: patiente.gender. If some day this go ok, there is a fixture,
# TODO: gender.json to load gender data and translations.
# class GenderTranslationOptions(TranslationOptions):
#     fields = ('name',)
#
#     # Have to set "translation_field.null = False" to manage.py makemigrations
#     # on Gender model to add translation fields in experiments_gender table.
#     # django-modeltranslation claims about translating primary key field with
#     # error:
#     #
#     # SystemCheckError: System check identified some issues:
#     # ERRORS:
#     # experiments.Gender.name_en: (fields.E007) Primary keys must not have
#     # null=True.
#     # 	   HINT: Set null=False on the field, or remove primary_key=True
#     # argument.
#     # experiments.Gender.name_pt_br: (fields.E007) Primary keys must not
#     # have null=True.
#     # 	   HINT: Set null=False on the field, or remove primary_key=True
#     # argument.
#     # Solution obtained inspired in
#     # https://github.com/deschler/django-modeltranslation/issues/144,
#     # commentary on 31 Oct 2016, by yerihyo.
#     # Related questions on stackoverflow:
#     # https://stackoverflow.com/questions/46779674/setting-django-model-primary-key-field-for-translation-with-django-modeltranslat
#     # and
#     # https://stackoverflow.com/questions/46787851/is-there-any-function-in-django-that-tests-if-a-field-instance-of-a-model-is-pri
#     def add_translation_field(self, field, translation_field):
#         translation_field.null = False
#         super(GenderTranslationOptions, self).add_translation_field(
#             field, translation_field
#         )
#
#
# translator.register(Gender, GenderTranslationOptions)
