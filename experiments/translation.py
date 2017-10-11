from modeltranslation.translator import TranslationOptions, translator

from experiments.models import ClassificationOfDiseases


class ClassificationOfDiseasesTranslationOptions(TranslationOptions):
    fields = ('description', 'abbreviated_description')


translator.register(
    ClassificationOfDiseases, ClassificationOfDiseasesTranslationOptions
)
