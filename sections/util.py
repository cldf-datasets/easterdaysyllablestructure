import re

import attr
from clldutils.misc import slug

__all__ = [
    'fix_bibkey', 'parse_refs', 'format_refs', 'convert_text', 'tex_pattern', 'iter_sections']


def iter_sections(p):
    return iter_chunks(iter_lines(p), lambda l: l.startswith('\\section*'), Section)


def fix_bibkey(t):
    return slug(t, lowercase=False)


def tex_pattern(cmd, braces='{}'):
    return re.compile('\\\\%s\*?%s(?P<text>[^%s]+)%s' % (
        re.escape(cmd), re.escape(braces[0]), re.escape(braces[1]), re.escape(braces[1])))


def format_refs(refs):
    def fmt(r):
        res = r[0]
        if r[1]:
            res += '[{0}]'.format(r[1])
        return res
    return [fmt(r) for r in refs]


def parse_refs(s, strip=False):
    refs = set()

    def repl(m):
        d = m.groupdict()
        pages = d.get('pagesa') or d.get('pagesb') or d.get('pages')
        refs.add((fix_bibkey(m.group('ref')), (pages.strip() or None) if pages else None))
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
class Item(object):
    headline = attr.ib()
    lines = attr.ib()
    name = attr.ib(default=None)
    value = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.name = tex_pattern('item', braces='[]').match(self.headline).group('text').strip()
        if self.name.endswith(':'):
            self.name = self.name[:-1].strip()
        if self.name == 'Category':
            self.name = 'Complexity category'
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
