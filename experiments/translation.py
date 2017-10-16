from modeltranslation.translator import TranslationOptions, translator

from experiments.models import ClassificationOfDiseases, Gender


class ClassificationOfDiseasesTranslationOptions(TranslationOptions):
    fields = ('description', 'abbreviated_description')


translator.register(
    ClassificationOfDiseases, ClassificationOfDiseasesTranslationOptions
)


# class GenderTranslationOptions(TranslationOptions):
#     fields = ('name',)
#
#
# translator.register(Gender, GenderTranslationOptions)
