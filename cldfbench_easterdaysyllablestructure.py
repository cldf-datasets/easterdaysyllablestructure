import re
import pathlib
import collections

from cldfbench import Dataset as BaseDataset, CLDFSpec
from clldutils.misc import slug

from sections.util import *
from sections import PARAM_CLASSES


def code_id(param, code):
    f = base16 if param.endswith('_inventory') else slug
    return '{0}-{1}'.format(param, f(code))


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "easterdaysyllablestructure"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_readme(self, args):
        lines, title_found = [], False
        for line in super().cmd_readme(args).split('\n'):
            lines.append(line)
            if line.startswith('# ') and not title_found:
                title_found = True
                lines.extend([
                    '',
                    "[![Build Status](https://travis-ci.org/cldf-datasets/easterdaysyllablestructure.svg?branch=master)]"
                    "(https://travis-ci.org/cldf-datasets/easterdaysyllablestructure)"
                ])
        return '\n'.join(lines)

    def cmd_download(self, args):
        #
        # We download the TeX source of appendix and bibliography of the LSP book.
        #
        BASE_URL = 'https://raw.githubusercontent.com/langsci/249/master/'
        self.raw_dir.download(BASE_URL + 'chapters/appendixB.tex', 'data.tex')
        self.raw_dir.download(BASE_URL + 'localbibliography.bib', 'sources.bib')
        lines = []
        at_line_pattern = re.compile('@(?P<type>[a-z]+){(?P<key>[^,]+),')
        # Make sure BibTeX keys are ASCII-only:
        for line in self.raw_dir.read('sources.bib').split('\n'):
            m = at_line_pattern.match(line)
            if m:
                line = '@{0}{{{1},'.format(m.group('type'), fix_bibkey(m.group('key')))
            lines.append(line)
        self.raw_dir.write('sources.bib', '\n'.join(lines))

    def cmd_makecldf(self, args):
        #
        # Turning the TeX data into a CLDF dataset is a multistep process:
        # 1. We split the TeX source into sections, subsections and items.
        # 2. We convert the text data into structured data, using the `sections` package.
        # 3. We split the structured data into bits suitable as atomic values of parameters.
        #
        args.writer.cldf.add_component(
            'LanguageTable',
            {
                "name": "Source",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
                "separator": ";"
            },
        )
        args.writer.cldf.add_component(
            'ParameterTable',
            'Section',
            'datatype',
            {
                'name': 'multichoice',
                'datatype': {'base': 'boolean', 'format': 'yes|no'},
                'dc:description': 'Whether a parameter may have multiple values per language',
            })
        args.writer.cldf.add_component('CodeTable')
        sources = collections.OrderedDict([(e.id, e) for e in self.raw_dir.read_bib()])
        lname2gc = {
            l['Name']: l['Glottocode'] for l in self.etc_dir.read_csv('languages.csv', dicts=True)}
        liso2gl = {l.iso: l for l in args.glottolog.api.languoids() if l.iso}

        multichoice = {}
        for n, cls in PARAM_CLASSES.items():
            for name, datatype, _, _ in cls().parameters:
                args.writer.objects['ParameterTable'].append({
                    'ID': name,
                    'Name': name.replace('_', ' '),
                    'Section': n.replace('_', ' '),
                    'datatype': 'categorical' if isinstance(datatype, (list, tuple)) or datatype == 'multichoice'
                    else datatype,
                    'multichoice': datatype == 'multichoice',
                })
                if datatype == 'multichoice':
                    multichoice[name] = set()
                if isinstance(datatype, (list, tuple)):
                    for opt in datatype:
                        args.writer.objects['CodeTable'].append({
                            'ID': code_id(name, opt),
                            'Name': opt,
                            'Parameter_ID': name,
                        })
        process_params = {
            'Vowel reduction processes': 'R',
            'Consonant allophony processes': 'C',
        }
        process_value_pattern = re.compile('(?P<iso>[a-z]{3})-(?P<pid>[RC])(?P<no>[0-9]+)$')
        for name, id_ in process_params.items():
            args.writer.objects['ParameterTable'].append({
                'ID': id_,
                'Name': name,
                'Section': 'Processes',
                'datatype': 'string',
                'multichoice': True,
            })

        phonemes = collections.Counter()
        nval = 0
        for sec in iter_sections(self.raw_dir / 'data.tex'):
            glang = liso2gl[sec.iso]
            lkw = {
                'ID': sec.iso,
                'Name': sec.name,
                'ISO639P3code': sec.iso,
                'Glottocode': lname2gc.get(sec.name, glang.id),
                'Latitude': glang.latitude,
                'Longitude': glang.longitude,
                'Macroarea': glang.macroareas[0].name,
                'Source': sec.refs,
            }
            args.writer.objects['LanguageTable'].append(lkw)
            args.writer.cldf.add_sources(*[sources[ref] for ref in sec.refs])
            data = {k: {} for k in PARAM_CLASSES}
            for ss in sec.subsections:
                for item in ss.items:
                    if sec.iso == 'yue' and item.name == 'N consonant phonemes':
                        # https://github.com/langsci/249/issues/1
                        item.name = 'C phoneme inventory'

                    if item.attribute == 'Phonetic_correlates_of_stress' and ss.name != 'Suprasegmentals':
                        # https://github.com/langsci/249/issues/3
                        assert sec.name == 'Towa'
                        data['Suprasegmentals'][item.attribute] = item.value
                    elif ss.name in data:
                        data[ss.name][item.attribute] = item.value
                    else:
                        assert process_value_pattern.match(item.name) or item.name == 'Notes'
                        text, refs = convert_text(item.value, warn_only=True)
                        nval += 1
                        args.writer.objects['ValueTable'].append({
                            'ID': str(nval),
                            'Language_ID': sec.iso,
                            'Parameter_ID': process_params[ss.name],
                            'Value': text,
                            'Comment': item.name,
                            'Source': format_refs(refs),
                        })

            data = {k: PARAM_CLASSES[k](**d) for k, d in data.items()}
            phonemes.update(data['Sound inventory'].C_phoneme_inventory)
            phonemes.update(data['Sound inventory'].V_phoneme_inventory)

            for n, cls in PARAM_CLASSES.items():
                for name, datatype, getter, refsgetter in cls().parameters:
                    v = getter(data[n])
                    refs = refsgetter(data[n]) if refsgetter else []
                    if v:
                        args.writer.cldf.add_sources(*[sources[r[0]] for r in refs])
                        if datatype == 'multichoice':
                            for vv in v:
                                multichoice[name].add(vv)
                                nval += 1
                                args.writer.objects['ValueTable'].append({
                                    'ID': str(nval),
                                    'Language_ID': sec.iso,
                                    'Parameter_ID': name,
                                    'Value': vv,
                                    'Source': format_refs(refs),
                                    'Code_ID': code_id(name, vv)
                                })
                        else:
                            nval += 1
                            kw = {
                                'ID': str(nval),
                                'Language_ID': sec.iso,
                                'Parameter_ID': name,
                                'Value': v,
                                'Source': format_refs(refs),
                            }
                            if isinstance(datatype, (list, tuple)):
                                kw['Code_ID'] = code_id(name, v)
                            args.writer.objects['ValueTable'].append(kw)

        for name, opts in multichoice.items():
            for opt in sorted(opts):
                args.writer.objects['CodeTable'].append({
                    'ID': code_id(name, opt),
                    'Name': opt,
                    'Parameter_ID': name,
                })
