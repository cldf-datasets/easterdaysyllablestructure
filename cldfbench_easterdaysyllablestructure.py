import re
import pathlib
import collections

from cldfbench import Dataset as BaseDataset, CLDFSpec
from clldutils.misc import slug

from sections.util import *
from sections import PARAM_CLASSES


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
        args.writer.cldf.add_component(
            'ParameterTable',
            'datatype',
            {
                'name': 'multichoice',
                'datatype': {'base': 'boolean', 'format': 'yes|no'},
                'dc:description': 'Whether a parameter may have multiple values per language',
            })
        args.writer.cldf.add_component('CodeTable')
        sources = collections.OrderedDict([(e.id, e) for e in self.raw_dir.read_bib()])

        multichoice = {}
        for n, cls in PARAM_CLASSES.items():
            for name, datatype, _, _ in cls().parameters:
                args.writer.objects['ParameterTable'].append({
                    'ID': name,
                    'Name': name.replace('_', ' '),
                    'datatype': 'categorical' if isinstance(datatype, (list, tuple)) or datatype == 'multichoice' else datatype,
                })
                if datatype == 'multichoice':
                    multichoice[name] = set()
                if isinstance(datatype, (list, tuple)):
                    for opt in datatype:
                        args.writer.objects['CodeTable'].append({
                            'ID': '{0}-{1}'.format(name, slug(opt)),
                            'Name': opt,
                            'Parameter_ID': name,
                        })

        phonemes = collections.Counter()
        nval = 0
        secs = collections.Counter()
        codes = collections.defaultdict(set)
        for i, sec in enumerate(iter_sections(self.raw_dir / 'data.tex'), start=1):
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
                                    'Language_ID': str(i),
                                    'Parameter_ID': name,
                                    'Value': v,
                                    'Source': format_refs(refs),
                                    'Code_ID': '{0}-{1}'.format(name, slug(vv))
                                })
                        else:
                            nval += 1
                            kw = {
                                'ID': str(nval),
                                'Language_ID': str(i),
                                'Parameter_ID': name,
                                'Value': v,
                                'Source': format_refs(refs),
                            }
                            if isinstance(datatype, (list, tuple)):
                                kw['Code_ID'] = '{0}-{1}'.format(name, slug(v))
                            args.writer.objects['ValueTable'].append(kw)

        for name, opts in multichoice.items():
            print('---', name)
            for opt in sorted(opts):
                print(opt)
                args.writer.objects['CodeTable'].append({
                    'ID': '{0}-{1}'.format(name, slug(opt)),
                    'Name': opt,
                    'Parameter_ID': name,
                })

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

        #for k, v in phonemes.most_common():
        #    print(k, v)
        #print(len(phonemes))





