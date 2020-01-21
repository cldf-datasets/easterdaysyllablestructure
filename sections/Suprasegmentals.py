"""
"""
import attr

from .util import *

PC = {}

STRESS_PLACEMENT = {
    'Fixed': 'Fixed',
    'Weight-sensitive': 'Weight-sensitive',
    'Not described': 'Not described',
    'Unpredictable/variable': 'Unpredictable/variable',
    'Morphologically or lexically conditioned': 'Morphologically or lexically conditioned',
    'Other (tone)': 'Other (tone)',
    'Other (tone and weight)': 'Other (tone and weight)',
}


def convert_word_stress(s):
    if not s:
        return None, None, []
    comment, refs = None, []
    if '(' in s:
        s, comment = s.split('(', maxsplit=1)
        if comment.endswith('.'):
            comment = comment[:-1]
        if not comment.endswith(')'):
            raise ValueError(s + '(' + comment)
        comment = comment[:-1].strip()
        s = s.strip()
        comment, refs = convert_text(comment)
    return s, comment, refs


@attr.s
class Suprasegmentals(object):
    # (none) / Not described
    Differences_in_phonological_properties_of_stressed_and_unstressed_syllables = attr.ib(default=None)
    Notes = attr.ib(default=None, converter=convert_text)
    Phonetic_correlates_of_stress = attr.ib(
        default=None,
        converter=lambda s: None if not s else [PC.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    Phonetic_processes_conditioned_by_stress = attr.ib(
        default=None,
        converter=lambda s: None if (not s or (s == '(none)')) else [{}.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    Stress_placement = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(list(STRESS_PLACEMENT.values())))
    )
    Tone = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(['No', 'Not reported', 'Yes']))
    )
    Word_stress = attr.ib(default=None, converter=convert_word_stress)

    @property
    def parameters(self):
        return [
            (
                'Differences_in_phonological_properties_of_stressed_and_unstressed_syllables',
                'string',
                lambda i: i.Differences_in_phonological_properties_of_stressed_and_unstressed_syllables,
                None),
            (
                'Suprasegmentals_notes',
                'string',
                lambda i: i.Notes[0] if i.Notes else None,
                lambda i: i.Notes[1] if i.Notes else []),
            (
                'Phonetic_correlates_of_stress', 'multichoice', lambda i: i.Phonetic_correlates_of_stress, None),
            (
                'Phonetic_processes_conditioned_by_stress', 'multichoice', lambda i: i.Phonetic_processes_conditioned_by_stress, None),
            (
                'Stress_placement',
                list(STRESS_PLACEMENT.values()),
                lambda i: i.Stress_placement,
                None),
            (
                'Tone',
                attr.fields_dict(Suprasegmentals)['Tone'].validator.validator.options,
                lambda i: i.Tone,
                None),
            (
                'Word_stress',
                ['Disagreement', 'No', 'Yes', 'Not reported'],
                lambda i: i.Word_stress[0] if i.Word_stress else None,
                lambda i: i.Word_stress[2] if i.Word_stress else None),
            (
                'Word_stress_comment',
                'string',
                lambda i: i.Word_stress[1] if i.Word_stress else None,
                lambda i: i.Word_stress[2] if i.Word_stress else None),
        ]
