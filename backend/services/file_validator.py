from email import policy
from email.parser import BytesParser
from pathlib import Path
import zipfile
import pymupdf
from defusedxml import ElementTree
from backend.config import MAX_FILE_SIZE, MAX_FILE_SIZE_MB, MAX_PAGES
from backend.services.errors import ConversionError

ALLOWED_MIMES = {
    'pdf': {'application/pdf'},
    'docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/zip'},
    'mht': {'message/rfc822', 'multipart/related', 'application/x-mimearchive', 'application/x-mime'},
    'mhtml': {'message/rfc822', 'multipart/related', 'application/x-mimearchive', 'application/x-mime'},
}


def read_mime_html(path: Path) -> str:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    if not message.is_multipart() or message.get_content_type() != 'multipart/related':
        raise ConversionError('O arquivo não é um documento MHT/MHTML válido.')
    html_parts = [p for p in message.walk() if p.get_content_type() == 'text/html']
    if not html_parts:
        raise ConversionError('Não foi encontrada uma página HTML neste arquivo.')
    root_id = message.get_param('start')
    part = next((p for p in html_parts if root_id and p.get('Content-ID') == root_id), html_parts[0])
    try:
        return (part.get_payload(decode=True) or b'').decode(part.get_content_charset() or 'utf-8', errors='replace')
    except LookupError:
        raise ConversionError('A codificação deste documento não é suportada.') from None


def validate_file(path: Path, extension: str, content_type: str | None) -> None:
    size = path.stat().st_size
    if not size:
        raise ConversionError('O arquivo está vazio.')
    if size > MAX_FILE_SIZE:
        raise ConversionError(f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.')
    mime = (content_type or '').split(';')[0].lower().strip()
    # Browsers often send octet-stream for MHT: signature validation remains mandatory.
    if mime not in ALLOWED_MIMES[extension] | {'', 'application/octet-stream'}:
        raise ConversionError('O tipo de conteúdo não corresponde ao formato do arquivo.')
    try:
        if extension == 'pdf':
            with path.open('rb') as handle:
                if not handle.read(8).startswith(b'%PDF-'):
                    raise ConversionError('O arquivo não possui uma assinatura PDF válida.')
            with pymupdf.open(path) as doc:
                if doc.needs_pass:
                    raise ConversionError('Este PDF está protegido por senha. Envie uma cópia desbloqueada.')
                if not 0 < len(doc) <= MAX_PAGES:
                    raise ConversionError(f'O PDF deve conter entre 1 e {MAX_PAGES} páginas.')
        elif extension == 'docx':
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                if len(members) > 5000 or sum(i.file_size for i in members) > 150 * 1024 * 1024:
                    raise ConversionError('O documento descompactado excede o limite de segurança.')
                if any(i.flag_bits & 1 or i.file_size > 50 * 1024 * 1024 for i in members):
                    raise ConversionError('O documento contém uma parte muito grande ou protegida.')
                names = set(archive.namelist())
                if not {'[Content_Types].xml', 'word/document.xml'} <= names:
                    raise ConversionError('O arquivo não possui a estrutura de um documento Word válido.')
                if any('vbaProject' in n or n.startswith('/') or '..' in n.split('/') for n in names):
                    raise ConversionError('Documentos com macros ou caminhos inseguros não são aceitos.')
                for item in members:
                    if item.filename.endswith(('.xml', '.rels')):
                        ElementTree.fromstring(archive.read(item))
        else:
            read_mime_html(path)
    except ConversionError:
        raise
    except Exception:
        raise ConversionError('O arquivo parece estar corrompido ou não corresponde ao formato informado.') from None
