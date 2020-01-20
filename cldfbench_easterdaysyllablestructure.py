import re
import pathlib
import collections

import attr
from cldfbench import Dataset as BaseDataset, CLDFSpec
from clldutils.misc import slug
from clldutils.text import strip_chars


def fix_bibkey(t):
    return slug(t, lowercase=False)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "easterdaysyllablestructure"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        BASE_URL = 'https://raw.githubusercontent.com/langsci/249/master/'
        self.raw_dir.download(BASE_URL + 'chapters/appendixB.tex', 'data.tex')
        self.raw_dir.download(BASE_URL + 'localbibliography.bib', 'sources.bib')
        bib = self.raw_dir.read('sources.bib')
        lines = []
        at_line_pattern = re.compile('@(?P<type>[a-z]+){(?P<key>[^,]+),')
        for line in self.raw_dir.read('sources.bib').split('\n'):
            m = at_line_pattern.match(line)
            if m:
                line = '@{0}{{{1},'.format(m.group('type'), fix_bibkey(m.group('key')))
            lines.append(line)
        self.raw_dir.write('sources.bib', '\n'.join(lines))

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        args.writer.cldf.add_component('LanguageTable')
        sources = collections.OrderedDict([(e.id, e) for e in self.raw_dir.read_bib()])

        secs = collections.Counter()
        codes = collections.defaultdict(set)
        for i, sec in enumerate(iter_chunks(
            iter_lines(self.raw_dir / 'data.tex'),
            lambda l: l.startswith('\\section*'),
            Section,
        ), start=1):
            print(i, sec)
            args.writer.objects['LanguageTable'].append({
                'ID': str(i),
                'Name': sec.name,
                'ISO639P3code': sec.iso,
            })
            args.writer.cldf.add_sources(*[sources[ref] for ref in sec.refs])
            data = {k: {} for k in PARAM_CLASSES}
            for ss in sec.subsections:
                #print('  {0}'.format(ss.name))
                secs.update([ss.name])
                for item in ss.items:

                    if sec.iso == 'yue' and item.name == 'N consonant phonemes':
                        item.name = 'C phoneme inventory'

                    if ss.name in data:
                        data[ss.name][item.attribute] = item.value
                    #print('    {0}: {1}'.format(item.name, item.value))
                    if not item.name.startswith('{0}-'.format(sec.iso)):
                        # There are language-specific parameters -> put in units!
                        codes[(ss.name, item.name)].add(item.value)
            data = {k: PARAM_CLASSES[k](**d) for k, d in data.items()}
            print(data['Syllable structure'])
            #for k, v in data.items():
            #    print(k)
            #    print(v)

        #for k, v in sorted(codes.items(), key=lambda i: i[0]):
            #print(k)
            #if len(v) > 10:
            #    print(len(v))
            #else:
            #    for vv in sorted(v):
            #        print('  {0}'.format(vv[:20]))

        #for k, v in secs.most_common():
        #    print(k, v)


def tex_pattern(cmd, braces='{}'):
    return re.compile('\\\\%s\*?%s(?P<text>[^%s]+)%s' % (
        re.escape(cmd), re.escape(braces[0]), re.escape(braces[1]), re.escape(braces[1])))


def parse_refs(s, strip=False):
    refs = set()

    def repl(m):
        d = m.groupdict()
        pages = d.get('pagesa') or d.get('pagesb') or d.get('pages')
        refs.add((m.group('ref'), (pages.strip() or None) if pages else None))
        if strip:
            return ''
        res = m.group('ref')
        if pages and pages.strip():
            res += ': {0}'.format(pages.strip())
        return res

    s = re.sub(
        '\\\\cite(p|t|year)(\[(?P<pages>[^\]]+)\])?{(?P<ref>[^}]+)}',
        repl,
        s)
    s = re.sub(
        '\\\\citealt(\[(?P<pagesa>[^\]]+)\])?{(?P<ref>[^}]+)}(:\s*(?P<pagesb>[0-9\-,\s]+))?',
        repl,
        s)
    return s, refs


def convert_text(s, strip=False):
    if not s:
        return None
    s, refs = parse_refs(s, strip=strip)
    s = tex_pattern('ili').sub(lambda m: m.group('text'), s)
    s = tex_pattern('textit').sub(lambda m: '*' + m.group('text') + '*', s)
    for k, v in {
        '\\%': '%',
        '{\\textasciitilde}': '~',
        '\\&': '&',
        '\\textsubscript{2}': '₂',
        '\\~{l}': 'l̃',
        '\\u{}': '̆ ',
    }.items():
        s = s.replace(k, v)

    s = tex_pattern('textsubscript').sub(lambda m: '<sub>' + m.group('text') + '</sub>', s)
    s = tex_pattern('textsuperscript').sub(lambda m: '<sup>' + m.group('text') + '</sup>', s)
    if '\\' in s:
        raise ValueError(s)
    return s, refs


@attr.s
class Morphology(object):
    """
    'Synthetic index' -> \item[Synthetic index:] 1.4 morphemes/word (639 morphemes, 455 words)
    'Text' -> \item[Text:] “Traditional village work” \citep[106--107]{Olsen2014}
    """
    Synthetic_index = attr.ib(
        default=None,
        converter=lambda s: Morphology.convert_synthetic_index(s),
    )
    Text = attr.ib(
        default=None,
        converter=convert_text,
    )

    @staticmethod
    def convert_synthetic_index(s):
        if not s:
            return None
        m = re.match(
            '\s*(?P<index>[0-9.]+)\s+morphemes/word\s+\((?P<m>[0-9]+)\s+morphemes,\s+(?P<w>[0-9]+)\s+words\)',
            s)
        return (float(m.group('index')), int(m.group('m')), int(m.group('w')))


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
        converter=lambda s: None if not s else [ss.strip() for ss in s.split(',')],
    )
    Geminates = attr.ib(
        default=None,
        converter=lambda s: None if (s == 'N/A' or (not s)) else s.split('(')[0].strip().split(),
    )
    Manners = attr.ib(
        default=None,
        converter=lambda s: None if not s else [ss.strip() for ss in s.split(',')],
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
        default=None)
    Places = attr.ib(
        default=None,
        converter=lambda s: None if not s else [ss.strip() for ss in s.split(',')],
    )
    V_phoneme_inventory = attr.ib(
        default=None,
        converter=lambda s: s.split() if s else [])
    Voicing_contrasts = attr.ib(
        default=None,
        converter=lambda s: None if (not s or (s == 'None')) else [ss.strip() for ss in s.split(',')],
    )

    def __attrs_post_init__(self):
        if self.C_phoneme_inventory and not self.N_consonant_phonemes:
            self.N_consonant_phonemes = len(self.C_phoneme_inventory)
        if not (self.N_consonant_phonemes or 0) in [len(self.C_phoneme_inventory), len(self.Geminates or [])]:
            raise ValueError(' '.join(self.C_phoneme_inventory))

    @staticmethod
    def convert_diphthongs_or_vowel_sequences(s):
        d, v, c = [], [], None
        if s == 'None':
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


@attr.s
class Suprasegmentals(object):
    # (none) / Not described
    Differences_in_phonological_properties_of_stressed_and_unstressed_syllables = attr.ib(default=None)
    Notes = attr.ib(default=None, converter=convert_text)
    Phonetic_correlates_of_stress = attr.ib(default=None)
    Phonetic_processes_conditioned_by_stress = attr.ib(default=None)
    Stress_placement = attr.ib(default=None)
    Tone = attr.ib(default=None)
    Word_stress = attr.ib(default=None)


@attr.s
class Syllable_structure(object):
    Canonical_syllable_structure = attr.ib(
        default=None,
        converter=lambda s: Syllable_structure.convert_canonical_syllable_structure(s),
    )
    Category = attr.ib(
        default=None,
    )
    Coda_obligatory = attr.ib(
        default=None,
        validator=attr.validators.in_(['N/A', 'No', 'Yes']),
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
        validator=attr.validators.in_(['No', 'Yes']),
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

    @staticmethod
    def convert_canonical_syllable_structure(s):
        template_pattern = re.compile('(?P<t>[()CV]+)\s+')
        m = template_pattern.match(s)
        assert m
        rem, refs = convert_text(s[m.end():], strip=True)
        rem = strip_chars('(),;.', rem).strip()
        if rem:
            raise ValueError(rem)
        return m.group('t'), refs

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

PARAM_CLASSES = {
    cls.__name__.replace('_', ' '): cls
    for cls in [Morphology, Sound_inventory, Suprasegmentals, Syllable_structure]}


@attr.s
class Item(object):
    headline = attr.ib()
    lines = attr.ib()
    name = attr.ib(default=None)
    value = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.name = tex_pattern('item', braces='[]').match(self.headline).group('text').strip()
        if self.name.endswith(':'):
            self.name = self.name[:-1].strip()
        self.value = self.headline.split(']', maxsplit=1)[1].strip()
        if self.lines:
            assert '\n'.join(self.lines).startswith('The processes below have quite a few')

    @property
    def attribute(self):
        return self.name.replace(' ', '_').replace('-', '_')


@attr.s
class Subsection(object):
    headline = attr.ib()
    lines = attr.ib()
    name = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.name = tex_pattern('subsection').match(self.headline).group('text')

    @property
    def items(self):
        return list(
            iter_chunks(self.lines, lambda l: l.startswith('\\item['), Item))


@attr.s
class Section(object):
    headline = attr.ib()
    lines = attr.ib()
    iso = attr.ib(default=None)
    name = attr.ib(default=None)
    lang_pattern = re.compile('\[(?P<iso>[a-z]{3})\]\s*(?P<name>[^}]+)')

    def __str__(self):
        return '{0.name} [{0.iso}]'.format(self)

    def __attrs_post_init__(self):
        text = self.headline
        if '\\ili{' in text:
            text = tex_pattern('ili').sub(lambda m: m.group('text'), text)
        m = self.lang_pattern.search(text)
        assert m
        self.iso = m.group('iso')
        self.name = m.group('name')

    @property
    def refs(self):
        res = []
        for line in self.lines:
            if line.startswith('References consulted'):
                for m in tex_pattern('citet').finditer(line):
                    res.append(fix_bibkey(m.group('text')))
                break
        return res

    @property
    def subsections(self):
        return list(
            iter_chunks(self.lines, lambda l: l.startswith('\\subsection*'), Subsection))


def iter_lines(p):
    for line in p.read_text(encoding='utf8').split('\n'):
        for p in {'\\newpage', '\\begin{appendixdesc}', '\\end{appendixdesc}'}:
            line = line.replace(p, '')
        line = line.strip()
        if line and not line.startswith('%') and not line.startswith('\\addxcontentsline'):
            yield line


def iter_chunks(l, condition, cls):
    lines, section = [], None

    for line in l:
        if condition(line):
            if section:
                yield cls(section, lines)
            lines, section = [], line
        else:
            lines.append(line)
    if section:
        yield cls(section, lines)


"""

('Sound inventory', 'Geminates')
  /bː dː ɡː mː nː lː w
  /bː tː dː kː ɡː ʔː p
  /bː tː dː tˤː dˤː kː
  /fː sː mː nː ɲː ŋː l
  /ɴː/, many others in
  N/A
('Sound inventory', 'Other contrasts')
  Creaky (Some)
  Creaky voice (some)
  Glottalization (All)
  Glottalization (some
  N/A
  None
  Voicing
  Voicing (Some)
  Voicing?
('Suprasegmentals', 'Differences in phonological properties of stressed and unstressed syllables')
11
('Suprasegmentals', 'Phonetic correlates of stress')
18
('Suprasegmentals', 'Phonetic processes conditioned by stress')
  (none)
  Consonant allophony 
  Consonant allophony 
  Consonant allophony 
  Vowel reduction
  Vowel reduction, Con
  Vowel reduction, Con
  Vowel reduction, Con
('Suprasegmentals', 'Stress placement')
  Fixed
  Morphologically or l
  Not described
  Other (tone and weig
  Other (tone)
  Unpredictable/variab
  Weight-sensitive
('Suprasegmentals', 'Tone')
  No
  Not reported
  Yes
('Suprasegmentals', 'Word stress')
  Disagreement (Innes 
  Disagreement (\citea
  No
  Not reported
  Yes
('Vowel reduction processes', 'Notes')
13
"""
