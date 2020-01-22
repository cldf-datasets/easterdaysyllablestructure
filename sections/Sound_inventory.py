import re

import attr

from .util import *


MANNERS = {
    'Flap/tap': 'Flap/Tap',
    'Central Approximant': 'Central approximant',
    'Lateral Approximant': 'Lateral approximant',
    'Stops': 'Stop',
}

ELABORATIONS = {
    'Voiced fricative/affricates': 'Voiced fricative/affricate',
    'Voiced fricatives/affricates': 'Voiced fricative/affricate',
}

PLACES = {
    'Bilabials': 'Bilabial',
    'Palato-Alveolar': 'Palato-alveolar',
}

VOICING_CONTRASTS = {
    'Obstruent': 'Obstruents',
}


def convert_other_contrasts(s):
    if s == 'None' or (not s):
        return None, None

    amount = None
    if '(' in s:
        s, amount = [ss.strip() for ss in s.split('(')]
        amount = amount.lower()
    if s.endswith('?'):
        amount = 'Maybe'
        s = s[:-1].strip()
    if s == 'Creaky':
        s = 'Creaky voice'
    return s, amount


@attr.s
class Sound_inventory(object):
    C_phoneme_inventory = attr.ib(
        default=None,
        converter=lambda s: s.split() if s else [])
    Contrastive_length = attr.ib(
        default=None,
        converter=lambda s: ('Some' if s == 'Yes' else s) if s else None,
        validator=attr.validators.optional(attr.validators.in_(['All', 'Some', 'None'])),
    )
    Contrastive_nasalization = attr.ib(
        default=None,
        converter=lambda s: ('Some' if s == 'Yes' else s) if s else None,
        validator=attr.validators.optional(attr.validators.in_(['All', 'Some', 'None'])),
    )
    Diphthongs_or_vowel_sequences = attr.ib(
        default=None,
        converter=lambda s: Sound_inventory.convert_diphthongs_or_vowel_sequences(s),
    )
    Elaborations = attr.ib(
        default=None,
        converter=lambda s: None if not s else [ELABORATIONS.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    Geminates = attr.ib(
        default=None,
        converter=lambda s: None if (s == 'N/A' or (not s)) else s.split('(')[0].strip().split(),
    )
    Manners = attr.ib(
        default=None,
        converter=lambda s: None if not s else [MANNERS.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    N_consonant_phonemes = attr.ib(
        default=None,
        converter=lambda s: int(s) if s else None)
    N_elaborated_consonants = attr.ib(
        default=None,
        converter=lambda s: int(s) if s else None)
    N_elaborations = attr.ib(
        default=None,
        converter=lambda s: int(s) if s else None)
    N_vowel_qualities = attr.ib(
        default=None,
        converter=lambda s: int(s) if s else None)
    Notes = attr.ib(default=None, converter=convert_text)
    Other_contrasts = attr.ib(
        default=None,
        converter=convert_other_contrasts,
    )
    Places = attr.ib(
        default=None,
        converter=lambda s: None if not s else [PLACES.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )
    V_phoneme_inventory = attr.ib(
        default=None,
        converter=lambda s: s.split() if s else [])
    Voicing_contrasts = attr.ib(
        default=None,
        converter=lambda s: None if (not s or (s == 'None')) else [VOICING_CONTRASTS.get(ss.strip(), ss.strip()) for ss in s.split(',')],
    )

    @property
    def parameters(self):
        return [
            (
                'Other_contrast',
                ['Creaky voice', 'Voicing', 'Glottalization', 'N / A'],
                lambda i: i.Other_contrasts[0] if i.Other_contrasts else None,
                None),
            (
                'Other_contrast_amount',
                ['Some', 'All', 'Maybe'],
                lambda i: i.Other_contrasts[1] if i.Other_contrasts else None,
                None),
            (
                'Sound_inventory_notes',
                'string',
                lambda i: i.Notes[0] if i.Notes else None,
                lambda i: i.Notes[1] if i.Notes else []),
            (
                'N_consonants', 'integer', lambda i: i.N_consonant_phonemes, None),
            (
                'N_elaborated_consonants', 'integer', lambda i: i.N_elaborated_consonants, None),
            (
                'N_elaborations', 'integer', lambda i: i.N_elaborations, None),
            (
                'N_vowel_qualities', 'integer', lambda i: i.N_vowel_qualities, None),
            (
                'Consonant_inventory', 'multichoice', lambda i: i.C_phoneme_inventory, None
            ),
            (
                'Vowel_inventory', 'multichoice', lambda i: i.V_phoneme_inventory, None,
            ),
            (
                'Geminate_inventory', 'multichoice', lambda i: i.Geminates, None
            ),
            (
                'Diphtong_inventory', 'multichoice', lambda i: i.Diphthongs_or_vowel_sequences[0], None,
            ),
            (
                'Vowel_sequence_inventory', 'multichoice', lambda i: i.Diphthongs_or_vowel_sequences[1], None,
            ),
            (
                'Comment_on_diphthongs_and_vowel_sequences', 'string', lambda i: i.Diphthongs_or_vowel_sequences[2], None,
            ),
            (
                'Contrastive_length',
                attr.fields_dict(Sound_inventory)['Contrastive_length'].validator.validator.options,
                lambda i: i.Contrastive_length,
                None
            ),
            (
                'Contrastive_nasalization',
                attr.fields_dict(Sound_inventory)['Contrastive_nasalization'].validator.validator.options,
                lambda i: i.Contrastive_nasalization,
                None
            ),
            (
                'Place', 'multichoice', lambda i: i.Places, None),
            (
                'Elaboration', 'multichoice', lambda i: i.Elaborations, None),
            (
                'Manner', 'multichoice', lambda i: i.Manners, None),
            (
                'Voicing_contrasts', 'multichoice', lambda i: i.Voicing_contrasts, None),
        ]

    def __attrs_post_init__(self):
        if self.C_phoneme_inventory and not self.N_consonant_phonemes:
            self.N_consonant_phonemes = len(self.C_phoneme_inventory)
        if not (self.N_consonant_phonemes or 0) in [len(self.C_phoneme_inventory), len(self.Geminates or [])]:
            raise ValueError(' '.join(self.C_phoneme_inventory))

    @staticmethod
    def convert_diphthongs_or_vowel_sequences(s):
        d, v, c = [], [], None
        if not s or (s == 'None'):
            return (d, v, c)
        m = re.search('Diphthong(s)?\s+(?P<d>[^V(]+)', s)
        if m:
            d = m.group('d').strip().split()
            s = s[:m.start()] + s[m.end():]
        m = re.search('Vowel sequence(s)?\s+(?P<v>[^D(]+)', s)
        if m:
            v = m.group('v').strip().split()
            s = s[:m.start()] + s[m.end():]
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            c = s[1:-1].strip()
            s = None
        assert not s
        return (d, v, c)
