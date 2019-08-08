from fman import load_json
from fman.fs import exists, is_dir
from fman.url import as_url

_USER_7ZIP = None
_SUPPORTED_EXTENSIONS = ['.7z', '.zip']
_CHECK_EXTENSION = True
_COMPRESS_ARGS = ['a']
_HASH = 'sha256'

settings = load_json('SevenZipTools.json', default={})
result = settings.get('7zip', {})
with open('R:/out.txt', 'w') as myfile:
    myfile.write(str(settings) + '\n')
if result:
    try:
        exePath = result['path']
    except (KeyError, TypeError):
        pass
    else:
        exePathUrl = as_url(exePath)
        if exists(exePathUrl) and not is_dir(exePathUrl):
            _USER_7ZIP = exePath
            _SUPPORTED_EXTENSIONS += ['.rar']

result = settings.get('additional extensions', [])
if result and isinstance(result, list):
    _SUPPORTED_EXTENSIONS += result

result = settings.get('ignore extension', None)
if result:
    _CHECK_EXTENSION = False

result = settings.get('compress args', [])
if result and isinstance(result, list):
    _COMPRESS_ARGS += result

result = settings.get('hash type', None)
if result:
    _HASH = result

result = settings.get('compare hash type', None)
if result:
    _COMPARE_HASH = result
else:
    _COMPARE_HASH = _HASH

with open('R:/out.txt', 'a') as myfile:
    myfile.write(str(_USER_7ZIP) + '\n')
    myfile.write(str(_SUPPORTED_EXTENSIONS) + '\n')
    myfile.write(str(_CHECK_EXTENSION) + '\n')
    myfile.write(str(_COMPRESS_ARGS) + '\n')
    myfile.write(str(_HASH) + '\n')
    myfile.write(str(_COMPARE_HASH))
