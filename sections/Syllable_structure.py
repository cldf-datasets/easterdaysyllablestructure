"""
('Syllable structure', 'Morphological constituency of maximal syllable margin')
15
('Syllable structure', 'Morphological pattern of syllabic consonants')
11
('Syllable structure', 'Notes')
68
('Syllable structure', 'Nucleus')

('Syllable structure', 'Onset restrictions')
67
('Syllable structure', 'Phonetic correlates of stress')
  Vowel duration (inst
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
('Syllable structure', 'Syllabic consonant patterns')
  Liquid
  N/A
  Nasal
  Nasal (Conflicting),
  Nasal, Liquid
  Nasal, Liquid, Obstr
  Nasal, Obstruent
  Nasals
  Obstruent (Conflicti
  Obstruents
"""
import re

import attr
from clldutils.text import strip_chars

from .util import *


@attr.s
class Syllable_structure(object):
    Canonical_syllable_structure = attr.ib(
        default=None,
        converter=lambda s: Syllable_structure.convert_canonical_syllable_structure(s),
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
    Onset_restrictions = attr.ib(default=None)
    Phonetic_correlates_of_stress = attr.ib(default=None)
    Predictability_of_syllabic_consonants = attr.ib(default=None)
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
    Size_of_maximal_word_marginal_sequences_with_syllabic_obstruents = attr.ib(default=None)
    Syllabic_consonant_patterns = attr.ib(default=None)
    Vocalic_nucleus_patterns = attr.ib(
        default=None,
        converter=lambda s: None if not s else [ss.strip() for ss in s.split(',')],
    )

    @property
    def parameters(self):
        return [
        ]

    @staticmethod
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
