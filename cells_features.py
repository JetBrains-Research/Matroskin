import nbformat
import ast
import io
import json
import re
import scispacy
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language
from collections import Counter

from db_structures import Cell, Code_cell, Md_cell


def get_code_cells(notebook: nbformat.NotebookNode):
    try:
        notebook_code_cells = [(num, ''.join(cell['source'])) for num, cell in
                               enumerate(notebook['cells'])
                               if cell['cell_type'] == 'code'
                               and cell.get('source') is not None
                               and not cell['source'].startswith('%')]

    except nbformat.reader.NotJSONError:
        notebook_code_cells = zip([0], [ntb_string])
    except Exception:
        notebook_code_cells = zip([], [])
    return notebook_code_cells


def get_md_cells(notebook: nbformat.NotebookNode):
    try:
        notebook_md_cells = [(num, ''.join(cell['source'])) for num, cell in
                               enumerate(notebook['cells'])
                               if cell.get('cell_type') == 'markdown' 
                               and cell.get('source') and type(
                               cell['source']) in [str, list]]
        nums, notebook_md_cells = map(list, zip(*notebook_md_cells))

    except nbformat.reader.NotJSONError:
        nums = [0]
        notebook_md_cells = [ntb_string]
    except Exception:
        nums = []
        notebook_md_cells = []
    return zip(nums, notebook_md_cells) 
    

def get_ast(notebook_code_cells: [str]):
    notebook_cells_ast = []
    for code_cell in notebook_code_cells:
        try:
            cell_ast = try_parse_cell(code_cell)
            notebook_cells_ast.append(cell_ast)
        except Exception:
            continue
    return notebook_cells_ast


def try_parse_cell(code_string):
    try:
        code_ast = ast.parse(code_string)
        return code_ast
    except SyntaxError as e:  # TODO: reconsider a way for handling magic functions
        code_string = code_string.splitlines()
        del code_string[e.lineno - 1]
        code_string = '\n'.join(code_string)
        return try_parse_cell(code_string)


def get_cell_id(notebook_id, conn):
    cell = Cell(notebook_id=notebook_id)
    conn.add(cell)
    conn.commit()
    return cell.cell_id


def get_imports_from_asts(cell_ast):
    cell_imports = []
    ast_nodes = list(ast.walk(cell_ast))
    for node in ast_nodes:
        if type(node) == ast.Import:
            cell_imports += [alias.name for alias in node.names]
        if type(node) == ast.ImportFrom:
            cell_imports += [f'{node.module}.{alias.name}' for alias in
                                    node.names]
    return cell_imports


def get_lines_count_from_asts(cell_ast):
    try:
        return max([node.lineno 
        for node in ast.walk(cell_ast) 
        if hasattr(node, 'lineno')])
    except:
        return 0


def get_sentences_count(cell):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(cell)
    sentence_tokens = [[token.text for token in sent] 
                        for sent in doc.sents]
    return len(sentence_tokens)


def get_words(cell):
    nlp = spacy.load('xx_ent_wiki_sm')
    doc = nlp(cell)

    words = [token.text.lower()
         for token in doc
         if not token.is_stop and not token.is_punct]
    return words


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()


def get_language(cell):
    nlp = spacy.load('en_core_web_sm')
    nlp.max_length = 2000000
    nlp.add_pipe('language_detector', last=True)
    doc = nlp(cell)
    return doc._.language['language']


def add_code_cells(nums_and_cells, notebook_id, conn) -> list:
    imports = []
    for num, cell in nums_and_cells:
        cell_ast = try_parse_cell(cell)
        cell_id = get_cell_id(notebook_id, conn)
        cell_imports = get_imports_from_asts(cell_ast)
        cell_lines = get_lines_count_from_asts(cell_ast)

        conn.add(Code_cell(
            cell_id=cell_id,
            cell_num=num,
            code_imports=" ".join(cell_imports),
            code_lines_count = cell_lines,
            code_chars_count =len(cell),
            source=cell
        ))
        imports.append(" ".join(cell_imports))

    conn.commit()
    return imports


def get_md_contents(cell_text) -> dict:
    latex_regex_1 = r'\$(.*)\$'
    latex_regex_2 = r'\\begin(.*)\\end'

    html_regex = r'<(.*)>'
    code_regex = r'`(.*)`'
    result = {
        'latex': False,
        'html': False,
        'code': False
    }  
    
    cell_text = cell_text.replace('\n', '')
    if re.findall(latex_regex_1, cell_text, re.MULTILINE) \
        or re.findall(latex_regex_2, cell_text, re.MULTILINE):
        result['latex'] = True
    if re.findall(html_regex, cell_text, re.MULTILINE):
        result['html'] = True
    if re.findall(code_regex, cell_text, re.MULTILINE):
        result['code'] = True
    return result


def clean_text(text):
    text = text.replace('\n', ' ').lower()
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub('[^\w+. ]+', '', text)
    text = re.sub(' +', ' ', text).lstrip().rstrip()
    return text


def add_md_cells(nums_and_cells, notebook_id, conn):
    for num, cell in nums_and_cells:
        cell_id = get_cell_id(notebook_id, conn)
        #sentences_count = get_sentences_count(cell)
        #language = get_language(cell)
        words = get_words(cell)
        cell_contents = get_md_contents(cell)
        #unique_words = Counter(words)
        #unique_string = " ".join(f"{key}-{value}" for key, value in unique_words.items())
        conn.add(Md_cell(
            cell_id=cell_id,
            cell_num=num,
            sentences_count=0, #sentences_count,
            words_count=0, #len(words),
            unique_words='0', #unique_string,
            cell_language='en', #language,
            latex=cell_contents['latex'],
            html=cell_contents['html'],
            code=cell_contents['code'],
            source=cell
        ))
    conn.commit()
