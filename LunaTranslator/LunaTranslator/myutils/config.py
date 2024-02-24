import json
import os


def tryreadconfig(path, default=None):
    try:
        path = os.path.join('./userconfig/', path)
        if os.path.exists(path) == False:
            path += '.tmp'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as ff:
                x = json.load(ff)
        else:
            x = default if default else {}
        return x
    except:
        return {}


def tryreadconfig2(path):
    path = os.path.join('./files/defaultconfig/', path)
    with open(path, 'r', encoding='utf-8') as ff:
        x = json.load(ff)
    return x


static_data = tryreadconfig2('static_data.json')
defaultpost = tryreadconfig2('postprocessconfig.json')
defaultglobalconfig = tryreadconfig2('config.json')
defaulterrorfix = tryreadconfig2('transerrorfixdictconfig.json')
dfmagpie10_config = tryreadconfig2('magpie10_config.json')
defaultnoun = tryreadconfig2('noundictconfig.json')
translatordfsetting = tryreadconfig2('translatorsetting.json')
ocrdfsetting = tryreadconfig2('ocrsetting.json')
ocrerrorfixdefault = tryreadconfig2('ocrerrorfix.json')

ocrerrorfix = tryreadconfig('ocrerrorfix.json')
globalconfig = tryreadconfig('config.json')
magpie10_config = tryreadconfig('magpie10_config.json')
postprocessconfig = tryreadconfig('postprocessconfig.json')
noundictconfig = tryreadconfig('noundictconfig.json')
transerrorfixdictconfig = tryreadconfig('transerrorfixdictconfig.json')
_savehook = tryreadconfig('savehook_new_1.39.4.json', default=[[], {}])
try:
    savehook_new_list = _savehook[0]
    savehook_new_data = _savehook[1]
except:
    savehook_new_list = []
    savehook_new_data = {}

translatorsetting = tryreadconfig('translatorsetting.json')
ocrsetting = tryreadconfig('ocrsetting.json')


def getdefaultsavehook(gamepath, title=None):
    default = {
        'localeswitcher': 0,
        'onloadautochangemode2': 0,
        'needinserthookcode': [],
        'embedablehook': [],
        'imagepath': None,
        'infopath': None,
        'vid': 0,
        'statistic_playtime': 0,
        'statistic_wordcount': 0,
        'statistic_wordcount_nodump': 0,
        'leuse': True,
        'hook': [],
        'inserthooktimeout': 0,
        'needinserthookcode': [],
        "removeuseless": False,
        "codepage_index": 0,
        "allow_tts_auto_names": '',
        "hooktypeasname": {},
        "use_saved_text_process": False,
        "fridahook": {},
        "searchnoresulttime": 0,
        'relationlinks': []
    }
    if gamepath == '0':
        default['title'] = 'No Game'
    elif title and len(title):
        default['title'] = title
    else:
        default['title'] = os.path.basename(os.path.dirname(gamepath)) + '/' + os.path.basename(gamepath)
    return default


_dfsavehook = getdefaultsavehook('')
for game in savehook_new_data:
    for k in _dfsavehook:
        if k not in savehook_new_data[game]:
            savehook_new_data[game][k] = _dfsavehook[k]


def syncconfig(config1, default, drop=False, deep=0, skipdict=False):
    for key in default:
        if key not in config1:
            config1[key] = default[key]

        elif key == 'name':
            config1[key] = default[key]
        if type(default[key]) != type(config1[key]) and (type(default[key]) == dict or type(default[key]) == list):
            config1[key] = default[key]
        elif type(default[key]) == dict:
            if skipdict == False:
                syncconfig(config1[key], default[key], drop, deep - 1)

    if drop and deep > 0:
        for key in list(config1.keys()):
            if key not in default:
                config1.pop(key)


syncconfig(globalconfig, defaultglobalconfig)
syncconfig(transerrorfixdictconfig, defaulterrorfix)

syncconfig(noundictconfig, defaultnoun)
syncconfig(magpie10_config, dfmagpie10_config, skipdict=True)
syncconfig(translatorsetting, translatordfsetting)

syncconfig(ocrsetting, ocrdfsetting)

if ocrerrorfix == {}:
    if '_100' in postprocessconfig:
        ocrerrorfix = postprocessconfig['_100']
    else:
        ocrerrorfix = ocrerrorfixdefault
syncconfig(postprocessconfig, defaultpost, True, 3)

if len(globalconfig['toolbutton']['rank']) != len(globalconfig['toolbutton']['buttons'].keys()):
    globalconfig['toolbutton']['rank'] += list(
        set(globalconfig['toolbutton']['buttons'].keys()) - set(globalconfig['toolbutton']['rank']))


def setlanguage():
    global language, languageshow
    language = globalconfig['languageuse']
    with open('./files/lang/{}.json'.format(static_data["language_list_translator_inner"][language]), 'r',
              encoding='utf8') as ff:
        languageshow = json.load(ff)


setlanguage()


def _TR(k):
    global language, languageshow
    if k == '':
        return ''
    try:
        k.encode('ascii')
        return k
    except:
        if '_' in k:
            splits = k.split('_')
            return '_'.join([_TR(_) for _ in splits])

        if k not in languageshow or languageshow[k] == '':
            languageshow[k] = ''
            return k
        else:
            return languageshow[k]


def _TRL(kk):
    x = []
    for k in kk:
        x.append(_TR(k))
    return x


def testpriv():
    fname = f'./userconfig/{os.getpid()}'
    with open(fname, 'w') as ff:
        ff.write('')
    os.remove(fname)


def saveallconfig():
    def safesave(fname, js):
        # 有时保存时意外退出，会导致config文件被清空
        with open(fname + '.tmp', 'w', encoding='utf-8') as ff:
            ff.write(json.dumps(js, ensure_ascii=False, sort_keys=False, indent=4))
        if os.path.exists(fname):
            os.remove(fname)
        os.rename(fname + '.tmp', fname)

    safesave('./userconfig/config.json', globalconfig)
    safesave('./userconfig/magpie10_config.json', magpie10_config)
    safesave('./userconfig/postprocessconfig.json', postprocessconfig)
    safesave('./userconfig/transerrorfixdictconfig.json', transerrorfixdictconfig)
    safesave('./userconfig/noundictconfig.json', noundictconfig)
    safesave('./userconfig/translatorsetting.json', translatorsetting)
    safesave('./userconfig/ocrerrorfix.json', ocrerrorfix)
    safesave('./userconfig/ocrsetting.json', ocrsetting)
    safesave('./userconfig/savehook_new_1.39.4.json', [savehook_new_list, savehook_new_data])
    safesave('./files/lang/{}.json'.format(static_data["language_list_translator_inner"][language]), languageshow)
