from importlib import import_module

CONVERTERS = {
    ('pdf', 'md'): 'pdf.pdf_to_markdown',
    ('docx', 'md'): 'docx.docx_to_markdown',
    ('mht', 'xlsx'): 'mht.mht_to_excel',
    ('mhtml', 'xlsx'): 'mht.mht_to_excel',
    ('pdf', 'docx'): 'pdf.pdf_to_word',
    ('pdf', 'xlsx'): 'pdf.pdf_to_excel',
    ('pdf', 'pptx'): 'pdf.pdf_to_powerpoint',
}


def get_converter(input_format, output_format):
    return import_module('backend.converters.' + CONVERTERS[input_format, output_format]).convert
