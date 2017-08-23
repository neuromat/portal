from django import forms
from django.utils.translation import ugettext as _
from haystack.forms import SearchForm


class NepSearchForm(SearchForm):
    q = forms.CharField(
        required=True, label='',
        widget=forms.TextInput(
            attrs={'type': 'search',
                   'placeholder': _('Type key terms/words to be searched'),
                   'class': 'search-box',
                   'data-toggle': 'tooltip',
                   'data-placement': 'bottom',
                   'title': _('You can use the modifiers AND, OR, NOT to '
                              'combine terms to search. For instance:\nterm1 '
                              'AND term2\nterm1 OR term2\nterm1 NOT '
                              'term2\nAll kind of combinations with AND, OR, '
                              'NOT are accepted in advanced searching.\nBy '
                              'default, searching for terms separated with '
                              'one or more spaces will apply the AND '
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
            attrs={'id': 'filter_box', 'class': 'selectpicker search-select'}
        )
    )

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        if not self.cleaned_data.get('q'):
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
        :param sqs: SearchQuerySet until now
        :return: SearchQuerySet object
        """
        words = iter(query.split())
        result = self.searchqueryset

        for word in words:
            try:
                if word == 'AND':
                    result = result.filter_and(content=words.__next__())
                elif word == 'OR':
                    # TODO: fail when changin order of the words. See
                    # TODO: functional test:
                    # TODO: test_search_with_OR_modifier_returns_correct_objects
                    result = result.filter_or(content=words.__next__())
                elif word == 'NOT':
                    result = result.exclude(content=words.__next__())
                else:
                    result = result.filter(content=word)
            except StopIteration:
                return result

        return result
