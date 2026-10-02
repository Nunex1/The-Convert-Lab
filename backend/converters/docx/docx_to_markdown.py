from pathlib import Path
import base64
import mammoth
from markdownify import markdownify


def convert(source: Path, target: Path) -> list[str]:
    @mammoth.images.img_element
    def image_data(image):
        with image.open() as stream:
            encoded = base64.b64encode(stream.read()).decode('ascii')
        return {'src': f'data:{image.content_type};base64,{encoded}'}

    with source.open('rb') as stream:
        result = mammoth.convert_to_html(stream, convert_image=image_data, external_file_access=False)
    text = markdownify(result.value, heading_style='ATX', bullets='-', strip=['script', 'style'])
    target.write_text(text.strip() + '\n', encoding='utf-8')
    return ['Elementos avançados do Word podem não ter equivalente em Markdown.'] if result.messages else []
