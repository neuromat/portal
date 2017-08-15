from django import forms
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

    filter = forms.ChoiceField(
        required=False, label='',
        choices=[
            ('eeg', 'EEG'), ('tms', 'TMS'), ('emg', 'EMG'),
            ('goalkeeper', 'Goalkeeper game phase'),
            ('cinematic', 'Cinematic measures'),
            ('stabilometry', 'Stabilometry'), ('answertime', 'Answer time'),
            ('psychophysical', 'Psychophysical measures'),
            ('verbal', 'Verbal answer'),
            ('psychometric', 'Psychometric scales'),
            ('unitary', 'Unitary register')
        ],
        widget=forms.Select(
            attrs=
            {'id': 'filter_box',
             'class': 'selectpicker search-select',
             'multiple': ''}
        )
    )

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super(NepSearchForm, self).search()

        if not self.is_valid():
            return self.no_query_found()

        return sqs
