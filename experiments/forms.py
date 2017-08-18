from django import forms
from django.utils.translation import ugettext as _
from haystack.forms import SearchForm


class NepSearchForm(SearchForm):
    q = forms.CharField(
        required=True, label='',
        widget=forms.TextInput(
            attrs={'type': 'search',
                   'placeholder': 'Type key terms/words to be searched',
                   'class': 'search-box'}
        )
    )

    filter = forms.MultipleChoiceField(
        required=False, label='',
        choices=[
            ('eeg', _('EEG')), ('tms', _('TMS')), ('emg', _('EMG')),
            ('goalkeeper', _('Goalkeeper game phase')),
            ('cinematic', _('Kinematic measures')),
            ('stabilometry', _('Stabilometry')),
            ('answertime', _('Response time')),
            ('psychophysical', _('Psychophysical measures')),
            ('verbal', _('Verbal response')),
            ('psychometric', _('Psychometric scales')),
            ('unitary', _('Unit recording')),
            ('multiunit', _('Multiunit recording'))
        ],
        widget=forms.SelectMultiple(
            attrs={'id': 'filter_box', 'class': 'selectpicker search-select'}
        )
    )

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super(NepSearchForm, self).search()

        if not self.is_valid():
            return self.no_query_found()

        return sqs
