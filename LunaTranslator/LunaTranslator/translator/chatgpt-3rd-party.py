from traceback import print_exc

import json
import requests

from translator.basetranslator import basetrans
import os


class TS(basetrans):
    def langmap(self):
        return {'zh': 'Simplified Chinese', 'ja': 'Japanese', 'en': 'English', 'ru': 'Russian', 'es': 'Spanish',
                'ko': 'Korean', 'fr': 'French', 'cht': 'Traditional Chinese', 'vi': 'Vietnamese', 'tr': 'Turkish',
                'pl': 'Polish', 'uk': 'Ukrainian', 'it': 'Italian', 'ar': 'Arabic', 'th': 'Thai'}

    def __init__(self, typename):
        self.context = []
        super().__init__(typename)

    def inittranslator(self):
        self.api_key = None

    def translate(self, query):
        os.environ['https_proxy'] = self.proxy['https'] if self.proxy['https'] else ''
        os.environ['http_proxy'] = self.proxy['http'] if self.proxy['http'] else ''
        self.checkempty(['SECRET_KEY', 'model'])
        self.contextnum = int(self.config['附带上下文个数'])

        try:
            temperature = float(self.config['Temperature'])
        except:
            temperature = 0.3

        if self.config['使用自定义promt']:
            message = [
                {'role': 'user', 'content': self.config['自定义promt']}
            ]
        else:
            message = [
                {"role": "system", "content": "You are a translator"},
                {"role": "user", "content": "translate from {} to {}".format(self.srclang, self.tgtlang)},
            ]

        for _i in range(min(len(self.context) // 2, self.contextnum)):
            i = len(self.context) // 2 - min(len(self.context) // 2, self.contextnum) + _i
            message.append(self.context[i * 2])
            message.append(self.context[i * 2 + 1])
        message.append({"role": "user", "content": query})

        headers = {
            'Authorization': 'Bearer ' + self.multiapikeycurrent['SECRET_KEY'],
            'Content-Type': 'application/json',
        }

        data = '{ "model": ' + json.dumps(
            self.config['model']) + ', "stream": false, "temperature": ' + json.dumps(
            temperature) + ', "messages": ' + json.dumps(
            message) + ' }'
        if self.config['API接口地址'].endswith('/'):
            self.config['API接口地址'] = self.config['API接口地址'][:-1]
        response = self.session.post(self.config['API接口地址'] + '/chat/completions', headers=headers, data=data)
        try:
            response = response.json()
        except:
            raise Exception(response.text)

        try:
            message = response['choices'][0]['message']['content'].replace('\n\n', '\n').strip()
            self.context.append({"role": "user", "content": query})
            self.context.append({
                'role': "assistant",
                "content": message
            })
            return message
        except:
            raise Exception(json.dumps(response, ensure_ascii=False))
