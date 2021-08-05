import re

from .cell_processor import CellProcessor


class MdProcessor(CellProcessor):

    def __init__(self, cell_data, nlp=None):
        self.cell = cell_data

        self.task_mapping = {
            'cell_language': self.get_cell_language,
            'sentences_count': self.get_sentences_count,
            'unique_words': self.get_unique_words,
            'content': self.get_md_content,
        }

        self.nlp = nlp
        self.nlp_doc = self.nlp(self.cell['source']) if self.nlp else None

    def get_cell_language(self, cell) -> str:
        return self.nlp_doc._.language['language']

    def get_sentences_count(self, cell) -> int:
        sentence_tokens = [[token.text for token in sent]
                           for sent in self.nlp_doc.sents]
        return len(sentence_tokens)

    def get_unique_words(self, cell) -> str:
        words = [token.text.lower()
                 for token in self.nlp_doc
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