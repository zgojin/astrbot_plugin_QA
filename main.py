import re
import json
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register


@register("keyword_reply_plugin", "开发者姓名", "自定义关键词回复插件", "1.0.0")
class KeywordReplyPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        if config is None:
            config = {}
        self.config = config
        self.question_answer_pairs = self.load_qa_pairs()
        self.waiting_for_answer = False
        self.current_question = ""
        self.recording = False

    def load_qa_pairs(self):
        try:
            with open('qa_pairs.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_qa_pairs(self):
        with open('qa_pairs.json', 'w', encoding='utf-8') as f:
            json.dump(self.question_answer_pairs, f, ensure_ascii=False, indent=4)

    @filter.command("开始记录")
    async def start_recording(self, event: AstrMessageEvent):
        self.waiting_for_answer = False
        self.recording = True
        yield event.plain_result("正在记录")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        if self.waiting_for_answer:
            answer = event.message_obj.message.strip()
            self.question_answer_pairs[self.current_question] = answer
            self.waiting_for_answer = False
            self.recording = False
            self.save_qa_pairs()
            yield event.plain_result("已经成功记录问答")
        elif self.recording:
            question = event.message_obj.message.strip()
            self.current_question = question
            self.waiting_for_answer = True
            yield event.plain_result("已经记录问题，请继续输入回答")

    def is_recording(self):
        return self.recording

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def auto_reply(self, event: AstrMessageEvent):
        message = event.message_obj.message
        for question, answer in self.question_answer_pairs.items():
            if '%' in question:
                pattern = re.escape(question.strip('%'))
                if re.search(pattern, message):
                    yield event.plain_result(answer)
                    break
            else:
                if question == message:
                    yield event.plain_result(answer)
                    break
