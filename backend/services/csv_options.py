from backend.services.errors import ConversionError


def normalize_options(options=None):
    options = {} if options is None else options
    if (not isinstance(options, dict) or set(options) - {'delimiter', 'bom', 'sheet', 'protect_formulas'}
            or options.get('delimiter', ';') not in (';', ',')
            or type(options.get('bom', False)) is not bool
            or type(options.get('protect_formulas', True)) is not bool
            or not isinstance(options.get('sheet', ''), str)
            or len(options.get('sheet', '')) > 31):
        raise ConversionError('As opções de exportação CSV são inválidas.')
    return {'delimiter': options.get('delimiter', ';'), 'bom': options.get('bom', False),
            'sheet': options.get('sheet', ''), 'protect_formulas': options.get('protect_formulas', True)}
