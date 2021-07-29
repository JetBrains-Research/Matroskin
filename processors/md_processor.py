import re
from processors import CellProcessor


class MdProcessor(CellProcessor):

    def __init__(self, cell_data, nlp=None):
        super().__init__(cell_data)

        self.task_mapping = {
            'cell_language': self.get_cell_language,
            'sentences_count': self.get_sentences_count,
            'unique_words': self.get_unique_words,
            'content': self.get_md_content,
        }

        self.nlp = nlp

    def process_cell(self, tasks) -> dict:
        for function in {
            k: v
            for k, v in tasks.items()
            if (v and k in self.task_mapping.keys())
        }:
            self.cell[function] = self.task_mapping[function](self.cell)
        return self.cell

    def get_cell_language(self, cell):
        doc = self.nlp(cell['source'])
        return doc._.language['language']

    def get_sentences_count(self, cell):
        doc = self.nlp(cell['source'])
        sentence_tokens = [[token.text for token in sent]
                           for sent in doc.sents]
        return len(sentence_tokens)

    def get_unique_words(self, cell) -> str:
        doc = self.nlp(cell['source'])

        words = [token.text.lower()
                 for token in doc
                 if not token.is_stop and not token.is_punct]
        unique_words = set(words)
        return ' '.join(unique_words)

    @staticmethod
    def get_md_content(cell) -> dict:
        latex_regex_1 = r'\$(.*)\$'
        latex_regex_2 = r'\\begin(.*)\\end'

        html_regex = r'<(.*)>'
        code_regex = r'`(.*)`'
        result = {
            'latex': False,
            'html': False,
            'code': False
        }

        cell_text = cell['source'].replace('\n', '')
        if re.findall(latex_regex_1, cell_text, re.MULTILINE) \
                or re.findall(latex_regex_2, cell_text, re.MULTILINE):
            result['latex'] = True
        if re.findall(html_regex, cell_text, re.MULTILINE):
            result['html'] = True
        if re.findall(code_regex, cell_text, re.MULTILINE):
            result['code'] = True
        return result