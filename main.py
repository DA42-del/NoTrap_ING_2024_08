import json

import cv2
import jieba
import pandas as pd
import pypinyin
from PIL import Image
from pytesseract import image_to_string
from tencentcloud.common import credential  # 这里需要安装腾讯翻译sdk
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tmt.v20180321 import models, tmt_client

import speak
from braille_dict import *
from speak import str_to_mp3


class device:
    def __init__(self):
        self.word = pd.read_csv("word.csv", sep=">", on_bad_lines="skip")
        self.word_translation = pd.read_csv(
            "word_translation.csv", sep=",", on_bad_lines="skip"
        )

    def single_search(self, target_word):
        """
        search a single word's translation, uk's pronunciation and us's pronunciation based on the word's content

        :param target_word: the content of the word
        :type target_word: str
        :return: translation, uk's pronunciation, us's pronunciation
        :rtype: str, str, str
        :Example:
        >>> self.search("a")
        ("n.(A)As 或 A's  安(ampere);(a) art.一;n.字母A /[军] A...", '[ə]', '[e]')
        """
        word_line = self.word[self.word["vc_vocabulary"] == target_word]
        word_translation_line = self.word_translation[
            self.word_translation["word"] == target_word
        ]
        vc_phonetic_uk = word_line["vc_phonetic_uk"]
        vc_phonetic_us = word_line["vc_phonetic_us"]
        translation = word_translation_line["translation"]

        return (
            translation.to_string(index=False),
            vc_phonetic_uk.to_string(index=False),
            vc_phonetic_us.to_string(index=False),
        )

    def read(self, image_name="test.jpg", image_path=""):
        """
        read the image and return text

        :param image_name: the name of the image
        :type image_name: str
        :param image_path: the path of the image
        :type image_path: str
        :return: the text in the image
        :rtype: str
        :Example:
        >>> self.read("text.png", "Image/")
        hello world
        """
        return image_to_string(Image.open(image_path + image_name))

    def translate(self, text):
        """
        translate English text into Chinese

        :param text: the text to be translated
        :type text: str
        :return: the tranlation result
        :rtype: str
        :Example:
        >>> self.translate("hello world")
        你好世界
        """
        try:
            cred = credential.Credential(
                "AKIDPjGi8Pql4Rl1Ng4Rm2mkctBpLl5JPQSf",
                "PxcAWlv4ESZhoqARaiibPAqZP9nKl6O3",
            )
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tmt.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tmt_client.TmtClient(cred, "ap-beijing", clientProfile)

            req = models.TextTranslateRequest()
            req.SourceText = text  # 要翻译的语句
            req.Source = "en"  # 源语言类型
            req.Target = "zh"  # 目标语言类型
            req.ProjectId = 0

            resp = client.TextTranslate(req)
            data = json.loads(resp.to_json_string())
            return data["TargetText"]

        except TencentCloudSDKException as err:
            print(err)

    def speak(self, input_text):  # noqa: F811
        """
        receive text and generate human voice file in mp3 formation

        :param input_text: the text to be speak
        :type input_text: str
        :return: this function doesn't have return
        :rtype: None
        :Example:
        >>> self.speak("hello world")
        there will be no output here
        """
        str_to_mp3(
            appid="70b791ee",
            api_secret="M2M1ZTdhN2RlNTI5NTk2Y2RhOTNjNTMw",
            api_key="9ca4a8e057795e6a4d2a1a670915228e",
            url="wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/medd90fec",
            # 待合成文本
            text=input_text,
            # 发音人参数
            vcn="x4_lingxiaoxuan_oral",
            save_file_name="./voice.mp3",
        )

    def text_to_array(self, input_text=""):
        words = list(jieba.cut(input_text))

        braille_array = []  # 盲文点阵序列
        first_letter = []  # 声母序列
        final_letter = []  # 韵母序列
        for word in words:
            first_letter += pypinyin.pinyin(
                word, style=pypinyin.Style.INITIALS, heteronym=False
            )
            first_letter += [[" "]]
            final_letter += pypinyin.pinyin(
                word, style=pypinyin.Style.FINALS_TONE3, heteronym=False
            )
            final_letter += [[" "]]

        trans_map = {"g": "j", "k": "q", "h": "x"}

        for i in range(len(first_letter)):
            # 盲文变换规则
            if (
                first_letter[i][0] in ["z", "c", "s", "zh", "ch", "sh", "r"]
                and final_letter[i][0][:-1] == "i"
            ):
                final_letter[i][0] = final_letter[i][0][-1:]
            if first_letter[i][0] in ["g", "k", "h"] and final_letter[i][0][:-1] in [
                "i",
                "u",
                "v",
            ]:
                first_letter[i][0] = trans_map[first_letter[i][0]]

            braille_array += first_letter_to_array.get(first_letter[i][0], [])  # noqa: F405
            braille_array += final_letter_to_array.get(final_letter[i][0][:-1], [])  # noqa: F405
            braille_array += tone_to_array.get(final_letter[i][0][-1:], [])  # noqa: F405
        return braille_array


if __name__ == "__main__":
    # the following is a test program
    myDev = device()
    # # 阅读同一文件夹下的指定图片，并提取出相应的文字，这里测试文件是test.jpg
    # text = myDev.read("test.jpg")
    # print(f"文本识别： {text}")
    # # 调用api在线翻译英文文本
    # print(myDev.translate(text))
    # # 根据输入的文本，在同一文件夹下生成人声朗读的mp3文件
    # myDev.speak(
    #     "燕子去了，有再来的时候；杨柳枯了，有再青的时候；桃花谢了，有再开的时候。但是，聪明的，你告诉我，我们的日子为什么一去不复返呢？"
    # )
    # # 基于智能分词系统，将中文文本分词后转换成特殊风格的拼音，并插入空格，便于之后的盲文打印
    # test_text = "很高兴认识你"
    # print(myDev.text_to_pinyin(test_text))
    print(myDev.text_to_array("哭泣是吧"))
