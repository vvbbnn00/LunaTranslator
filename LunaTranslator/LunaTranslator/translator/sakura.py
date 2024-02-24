from traceback import print_exc
from translator.basetranslator import basetrans
import requests


# OpenAI
# from openai import OpenAI

class TS(basetrans):
    def langmap(self):
        return {"zh": "zh-CN"}

    def __init__(self, typename):
        self.timeout = 30
        self.api_url = ""
        self.history = {
            "ja": [],
            "zh": []
        }
        self.session = requests.Session()
        super().__init__(typename)

    def sliding_window(self, text_ja, text_zh):
        if text_ja == "" or text_zh == "":
            return
        self.history['ja'].append(text_ja)
        self.history['zh'].append(text_zh)
        if len(self.history['ja']) > int(self.config['附带上下文个数（必须打开利用上文翻译）']) + 1:
            del self.history['ja'][0]
            del self.history['zh'][0]

    def get_history(self, key):
        prompt = ""
        for q in self.history[key]:
            prompt += q + "\n"
        prompt = prompt.strip()
        return prompt

    def get_client(self, api_url):
        if api_url[-4:] == "/v1/":
            api_url = api_url[:-1]
        elif api_url[-3:] == "/v1":
            pass
        elif api_url[-1] == '/':
            api_url += "v1"
        else:
            api_url += "/v1"
        self.api_url = api_url
        # OpenAI
        # self.client = OpenAI(api_key="114514", base_url=api_url)

    def make_messages(self, query, history_ja=None, history_zh=None, **kwargs):
        messages = [
            {
                "role": "system",
                "content": "你是一个轻小说翻译模型，可以流畅通顺地以日本轻小说的风格将日文翻译成简体中文，并联系上下文正确使用人称代词，不擅自添加原文中没有的代词。"
            }
        ]
        if history_ja:
            messages.append({
                "role": "user",
                "content": f"将下面的日文文本翻译成中文：{history_ja}"
            })
        if history_zh:
            messages.append({
                "role": "assistant",
                "content": history_zh
            })

        messages.append(
            {
                "role": "user",
                "content": f"将下面的日文文本翻译成中文：{query}"
            }
        )
        return messages

    def send_request(self, query, is_test=False, **kwargs):
        extra_query = {
            'do_sample': bool(self.config['do_sample']),
            'num_beams': int(self.config['num_beams']),
            'repetition_penalty': float(self.config['repetition_penalty']),
        }
        messages = self.make_messages(query, **kwargs)
        try:
            # OpenAI
            # output = self.client.chat.completions.create(
            data = dict(
                model="sukinishiro",
                messages=messages,
                temperature=float(self.config['temperature']),
                top_p=float(self.config['top_p']),
                max_tokens=1 if is_test else int(self.config['max_new_token']),
                frequency_penalty=float(kwargs['frequency_penalty']) if "frequency_penalty" in kwargs.keys() else float(
                    self.config['frequency_penalty']),
                seed=-1,
                extra_query=extra_query,
                stream=False,
            )
            output = self.session.post(self.api_url + "/chat/completions", timeout=self.timeout, json=data).json()
        except requests.Timeout as e:
            raise ValueError(f"连接到Sakura API超时：{self.api_url}，当前最大连接时间为: {self.timeout}，请尝试修改参数。")

        except Exception as e:
            print(e)
            raise ValueError(
                f"无法连接到Sakura API：{self.api_url}，请检查你的API链接是否正确填写，以及API后端是否成功启动。")
        return output

    def translate(self, query):
        self.checkempty(['API接口地址'])
        self.timeout = self.config['API超时(秒)']
        if self.api_url == "":
            self.get_client(self.config['API接口地址'])
        frequency_penalty = float(self.config['frequency_penalty'])
        if not bool(self.config['利用上文信息翻译（通常会有一定的效果提升，但会导致变慢）']):
            output = self.send_request(query)
            completion_tokens = output["usage"]["completion_tokens"]
            output_text = output["choices"][0]["message"]["content"]

            if bool(self.config['fix_degeneration']):
                cnt = 0
                while completion_tokens == int(self.config['max_new_token']):
                    # detect degeneration, fixing
                    frequency_penalty += 0.1
                    output = self.send_request(query, frequency_penalty=frequency_penalty)
                    completion_tokens = output["usage"]["completion_tokens"]
                    output_text = output["choices"][0]["message"]["content"]
                    cnt += 1
                    if cnt == 2:
                        break
        else:
            # 实验性功能，测试效果后决定是否加入。
            # fallback = False
            # if self.config['启用日文上下文模式']:
            #     history_prompt = self.get_history('ja')
            #     output = self.send_request(history_prompt + "\n" + query)
            #     completion_tokens = output.usage.completion_tokens
            #     output_text = output.choices[0].message.content

            #     if len(output_text.split("\n")) == len(history_prompt.split("\n")) + 1:
            #         output_text = output_text.split("\n")[-1]
            #     else:
            #         fallback = True
            # 如果日文上下文模式失败，则fallback到中文上下文模式。
            # if fallback or not self.config['启用日文上下文模式']:

            history_prompt = self.get_history('zh')
            output = self.send_request(query, history_zh=history_prompt)
            completion_tokens = output["usage"]["completion_tokens"]
            output_text = output["choices"][0]["message"]["content"]

            if bool(self.config['fix_degeneration']):
                cnt = 0
                while completion_tokens == int(self.config['max_new_token']):
                    frequency_penalty += 0.1
                    output = self.send_request(query, history_zh=history_prompt, frequency_penalty=frequency_penalty)
                    completion_tokens = output["usage"]["completion_tokens"]
                    output_text = output["choices"][0]["message"]["content"]
                    cnt += 1
                    if cnt == 3:
                        output_text = "Error：模型无法完整输出或退化无法解决，请调大设置中的max_new_token！！！原输出：" + output_text
                        break
            self.sliding_window(query, output_text)
        return output_text
