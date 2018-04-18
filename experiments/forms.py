import shlex

from django import forms
from django.utils.translation import ugettext_lazy as _
from haystack.forms import SearchForm

from experiments.models import Experiment


class NepSearchForm(SearchForm):
    q = forms.CharField(
        required=False, label='',
        widget=forms.TextInput(
            attrs={'type': 'search',
                   'placeholder': _('Type key terms/words to be searched'),
                   'class': 'form-control',
                   'data-toggle': 'tooltip',
                   'data-placement': 'bottom',
                   'title': _('You can search for terms in quotes to search '
                              'for exact terms.\nYou can use the modifiers '
                              'AND, OR, NOT to '
                              'combine terms to search. For instance:\nterm1 '
                              'AND term2\nterm1 OR term2\nterm1 NOT '
                              'term2\nAll kind of combinations with AND, OR, '
                              'NOT are accepted in advanced searching.\nBy '
                              'default, searching for terms separated with '
                              'one or more spaces will apply the OR '
                              'modifier.')}
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
            attrs={'id': 'filter_box', 'class': 'form-control selectpicker',
                   'title': _('Select one or more data collection types')}
        )
    )

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        sqs = self._parse_query(self.cleaned_data['q'])

        if self.load_all:
            sqs = sqs.load_all()

        return sqs

    def _parse_query(self, query):
        """
        Parse query treating modifiers 'AND', 'OR', 'NOT' to make what they're
        supposed to.
        :param query: query entered in search input box in form
        :return: SearchQuerySet object
        """
        words = iter(shlex.split(query))
        result = self.searchqueryset

        for word in words:
            try:
                if word == 'AND':
                    result = result.filter_and(content=words.__next__())
                elif word == 'OR':
                    # TODO: fail when changing order of the words. See
                    # TODO: functional test:
                    # TODO: test_search_with_OR_modifier_returns_correct_objects
                    result = result.filter_or(content=words.__next__())
                elif word == 'NOT':
                    result = result.exclude(content=words.__next__())
                # if "word" is compounded of more than one non blank word the
                # term is inside quotes
                elif len(word.split()) > 1:
                    result = result.filter(content__exact=word)
                else:
                    result = result.filter(content=word)
            except StopIteration:
                return result

        return result


EMPTY_SLUG_ERROR = 'Please give a non-blank experiment slug'


class ChangeSlugForm(forms.models.ModelForm):

    class Meta:
        model = Experiment
        fields = ('slug',)
        widgets = {
            'slug': forms.fields.TextInput(attrs={
                'placeholder': 'Type new slug',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'slug': {'required': EMPTY_SLUG_ERROR}
        }
