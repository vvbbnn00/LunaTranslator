from traceback import print_exc

import requests

from myutils.config import globalconfig
from translator.basetranslator import basetrans
import json


class TS(basetrans):
    def translate(self, query):
        self.checkempty(['Token'])

        token = self.multiapikeycurrent['Token']

        url = "http://api.interpreter.caiyunai.com/v1/translator"
        # WARNING, this token is a test token for new developers,
        # and it should be replaced by your token

        payload = {
            "source": query,
            "trans_type": self.srclang + '2' + self.tgtlang,
            "request_id": "demo",
            "detect": True,
        }
        headers = {
            "content-type": "application/json",
            "x-authorization": "token " + token,
        }
        response = self.session.request("POST", url, data=json.dumps(payload), headers=headers)
        try:
            res = json.loads(response.text)["target"]

            self.countnum(query)
            # print(res['trans_result'][0]['dst'])
            return res
        except:
            raise Exception(response.text)
