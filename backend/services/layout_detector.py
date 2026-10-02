"""Conservative eligibility for editable slide reconstruction."""


def editable_page(page, blocks) -> bool:
    if page.rotation or page.get_drawings() or page.get_images():
        return False
    spans = [s for b in blocks if b['type'] == 0 for line in b['lines'] for s in line['spans']]
    if not spans or len(spans) > 120:
        return False
    return all(line.get('dir') == (1.0, 0.0) for b in blocks if b['type'] == 0 for line in b['lines'])
