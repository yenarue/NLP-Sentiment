import re
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import six


# 참고 : https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/language/sentiment/sentiment_analysis.py
def analyze_sentiment(content):
    # [START language_sentiment_text_core]

    client = language.LanguageServiceClient()

    if isinstance(content, six.binary_type):
        content = content.decode('utf-8')

    # document = {'type': type_, 'content': content, 'language': 'ko'}
    encoding_type = enums.EncodingType.UTF8

    document = types.Document(
        content=content,
        type=enums.Document.Type.PLAIN_TEXT,
        language='ko'
    )

    # print(document)
    response = client.analyze_sentiment(document=document, encoding_type=encoding_type)
    doc_sentiment = response.document_sentiment
    print('Score: {}'.format(doc_sentiment.score))
    print('Magnitude: {}'.format(doc_sentiment.magnitude))

    return doc_sentiment.score, doc_sentiment.magnitude, response.sentences


def analyze_sentiment_each_sentence(feedback):
    # 개별 문장으로 연산
    sentences = re.split("[.!?~]\s+", feedback)
    print(sentences)
    print('문장 개수 : {}'.format(len(sentences)))

    total_score, total_magnitude = 0, 0
    for sentence in sentences:
        print("")
        print(sentence)
        score, magnitude, _ = analyze_sentiment(sentence)
        total_score += score
        total_magnitude += magnitude

    print("=========================")
    print('평균 Score : {}'.format(total_score / len(sentences)))
    print('평균 Magnitude : {}'.format(total_score / len(sentences)))
    print("=========================")


def analyze_sentiment_context(feedback, is_verbose):
    # 통채로 연산 => 컨텍스트까지 고려됨
    print("한꺼번에 구했을 때의 총 점수 : ")
    score, magnitude, doc_sentences = analyze_sentiment(feedback)
    print(str(len(doc_sentences)) + "개의 문장")
    print("")

    if is_verbose:
        # 통채로 연산한 결과의 세부 내용 확인 (각 문장 분석)
        print("한꺼번에 구했을 때의 세부 내용들 : ")
        total_doc_score, total_doc_magnitude = 0, 0
        for (index, sentence) in enumerate(doc_sentences):
            print(str(index + 1) + "번째 문장 : " + sentence.text.content)
            print(sentence.sentiment)
            total_doc_score += sentence.sentiment.score
            total_doc_magnitude += sentence.sentiment.magnitude

        print("각 문장의 평균")
        print("Score : " + str(total_doc_score / len(doc_sentences)))
        print("Magnitude : " + str(total_doc_magnitude / len(doc_sentences)))


# 띄어쓰기 검사기 돌려랏
feedback = '피드백데이터넣기'
# analyze_sentiment_each_sentence(feedback)
analyze_sentiment_context(feedback, False)
