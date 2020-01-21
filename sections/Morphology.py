"""
'Synthetic index' -> \item[Synthetic index:] 1.4 morphemes/word (639 morphemes, 455 words)
'Text' -> \item[Text:] “Traditional village work” \citep[106--107]{Olsen2014}
"""
import re

import attr

from .util import *


@attr.s
class Morphology(object):
    Synthetic_index = attr.ib(
        default=None,
        converter=lambda s: Morphology.convert_synthetic_index(s),
    )
    Text = attr.ib(
        default=None,
        converter=convert_text,
    )

    @property
    def parameters(self):
        return [
            ('Synthetic_index', 'number', lambda i: i.Synthetic_index[0], None),
            ('Synthetic_index_n_morphemes', 'integer', lambda i: i.Synthetic_index[1], None),
            ('Synthetic_index_n_words', 'integer', lambda i: i.Synthetic_index[2], None),
            ('Text', 'string', lambda i: i.Text[0] if i.Text else None, lambda i: i.Text[1] if i.Text else None),
        ]

    @staticmethod
    def convert_synthetic_index(s):
        if not s:
            return (None, None, None)
        m = re.match(
            '\s*(?P<index>[0-9.]+)\s+morphemes/word\s+\((?P<m>[0-9]+)\s+morphemes,\s+(?P<w>[0-9]+)\s+words\)',
            s)
        return (float(m.group('index')), int(m.group('m')), int(m.group('w')))
