"""
('Syllable structure', 'Predictability of syllabic consonants')
  N/A
  Phonemic
  Phonemic, Predictabl
  Predictable from wor
  Predictable from wor
  Unpredictable
  Varies with CV seque
  Varies with VC seque
  Varies with VC seque
('Syllable structure', 'Size of maximal word-marginal sequences with syllabic obstruents')
  2
  3 (initial), >3 (fin
  4 (initial)
  5 (initial), 3 (fina
  ? (words without vow
  N/A
  N/A (grammatical par
"""
import re

import attr
from clldutils.text import strip_chars

from .util import *

SCP = {
    'Obstruent (Conflicting reports)': 'Obstruent (Conflicting)',
}


def convert_canonical_syllable_structure(s):
    if not s:
        return None, []
    template_pattern = re.compile('(?P<t>[()CV]+)\s+')
    m = template_pattern.match(s)
    assert m
    rem, refs = convert_text(s[m.end():], strip=True)
    rem = strip_chars('(),;.', rem).strip()
    if rem:
        raise ValueError(rem)
    return m.group('t'), refs


@attr.s
class Syllable_structure(object):
    Canonical_syllable_structure = attr.ib(
        default=None,
        converter=convert_canonical_syllable_structure,
    )
    Coda_obligatory = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(['N/A', 'No', 'Yes'])),
    )
    Coda_restrictions = attr.ib(
        default=None,
        converter=convert_text,
    )
    Complexity_category = attr.ib(
        default=None,
        validator=attr.validators.optional(
            attr.validators.in_(['Highly Complex', 'Moderately Complex', 'Complex', 'Simple'])),
    )
    Morphological_constituency_of_maximal_syllable_margin = attr.ib(default=None)
    Morphological_pattern_of_syllabic_consonants = attr.ib(default=None)
    Notes = attr.ib(default=None, converter=convert_text)
    Nucleus = attr.ib(default=None)
    Onset_obligatory = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(['No', 'Yes'])),
    )
    Onset_restrictions = attr.ib(
        default=None,
        converter=convert_text,
    )
    Phonetic_correlates_of_stress = attr.ib(
        default=None,
        validator=attr.validators.instance_of(type(None)))
    Size_of_maximal_coda = attr.ib(
        default=None,
        converter=lambda s: None if (not s or (s == 'N/A')) else int(s),
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    Size_of_maximal_onset = attr.ib(
        default=None,
        converter=lambda s: None if (not s or (s == 'N/A')) else int(s),
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    Syllabic_consonant_patterns = attr.ib(
        default=None,
        converter=lambda s: None if not s else [SCP.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    Vocalic_nucleus_patterns = attr.ib(
        default=None,
        converter=lambda s: None if not s else [ss.strip() for ss in s.split(',')],
    )
    Predictability_of_syllabic_consonants = attr.ib(default=None)
    Size_of_maximal_word_marginal_sequences_with_syllabic_obstruents = attr.ib(default=None)

    @property
    def parameters(self):
        return [
            (
                'Predictability_of_syllabic_consonants',
                'string',
                lambda i: i.Predictability_of_syllabic_consonants,
                None),
            (
                'Size_of_maximal_word_marginal_sequences_with_syllabic_obstruents',
                'string',
                lambda i: i.Size_of_maximal_word_marginal_sequences_with_syllabic_obstruents, None),
            (
                'Complexity_category',
                attr.fields_dict(Syllable_structure)['Complexity_category'].validator.validator.options,
                lambda i: i.Complexity_category,
                None),
            (
                'Onset_obligatory',
                attr.fields_dict(Syllable_structure)['Onset_obligatory'].validator.validator.options,
                lambda i: i.Onset_obligatory,
                None),
            (
                'Coda_obligatory',
                attr.fields_dict(Syllable_structure)['Coda_obligatory'].validator.validator.options,
                lambda i: i.Coda_obligatory,
                None),
            (
                'Size_of_maximal_coda', 'integer', lambda i: i.Size_of_maximal_coda, None),
            (
                'Size_of_maximal_onset', 'integer', lambda i: i.Size_of_maximal_onset, None),
            (
                'Syllabic_consonant_patterns', 'multichoice', lambda i: i.Syllabic_consonant_patterns, None),
            (
                'Vocalic_nucleus_patterns', 'multichoice', lambda i: i.Vocalic_nucleus_patterns, None),
            (
                'Morphological_constituency_of_maximal_syllable_margin',
                'string',
                lambda i: i.Morphological_constituency_of_maximal_syllable_margin,
                None),
            (
                'Morphological_pattern_of_syllabic_consonants',
                'string',
                lambda i: i.Morphological_pattern_of_syllabic_consonants,
                None),
            (
                'Canonical_syllable_structure',
                'string',
                lambda i: i.Canonical_syllable_structure[0],
                lambda i: i.Canonical_syllable_structure[1]),
            (
                'Coda_restrictions',
                'string',
                lambda i: i.Coda_restrictions[0] if i.Coda_restrictions else None,
                lambda i: i.Coda_restrictions[1] if i.Coda_restrictions else []),
            (
                'Onset_restrictions',
                'string',
                lambda i: i.Onset_restrictions[0] if i.Onset_restrictions else None,
                lambda i: i.Onset_restrictions[1] if i.Onset_restrictions else []),
            (
                'Syllable_structure_notes',
                'string',
                lambda i: i.Notes[0] if i.Notes else None,
                lambda i: i.Notes[1] if i.Notes else []),
        ]
