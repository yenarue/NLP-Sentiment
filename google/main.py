import re
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import six
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas

def get_google_spread_sheet_workspace(spreadsheet_url):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]

    json_file_name = '../credentials.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)

    # 스프레스시트 문서 가져오기
    doc = gc.open_by_url(spreadsheet_url)
    # 시트 선택하기
    worksheet = doc.worksheet('설문지 응답 시트1')
    return worksheet

def get_feedback_dataframe(worksheet, feedback_col_title, email_col_title):
    data = worksheet.get_all_values()
    data_frame = pandas.DataFrame(data, columns=data[0])
    data_frame = data_frame.reindex(data_frame.index.drop(0))

    feedback_data_frame = pandas.DataFrame({
            "feedback": data_frame.loc[:, feedback_col_title],
            "email": data_frame.loc[:, email_col_title],
            "score": 0.0,
            "magnitude": 0.0,
            "sentence_count": 0,
            "feedback_length": 0,
            "positive_list": "",
            "neutral_list": "",
            "negative_list": "",
         })

    # feedbackDataFrame.at[1, 'score']
    return feedback_data_frame

# data_frame.loc[:, 'score']
def update_score_to_google_spreadsheet(worksheet, score_data_frame):
    list = score_data_frame.to_list()
    update_column_to_google_spreadsheet(worksheet, 'M2:M' + str(len(list) + 1), list)

def update_magnitude_to_google_spreadsheet(worksheet,magnitude_data_frame):
    list = magnitude_data_frame.to_list()
    update_column_to_google_spreadsheet(worksheet, 'N2:N' + str(len(list) + 1), list)

def update_sentence_count_to_google_spreadsheet(worksheet, sentence_count_data_frame):
    list = sentence_count_data_frame.to_list()
    update_column_to_google_spreadsheet(worksheet, 'O2:O' + str(len(list) + 1), list)

def update_feedback_length_to_google_spreadsheet(worksheet, data_frame):
    list = data_frame.to_list()
    update_column_to_google_spreadsheet(worksheet, 'P2:P' + str(len(list) + 1), list)

def update_each_sentence_scores_to_google_spreadsheet(worksheet, positive_list, neutral_list, negative_list):
    update_column_to_google_spreadsheet(worksheet, 'Q2:Q' + str(len(positive_list) + 1), positive_list.to_list())
    update_column_to_google_spreadsheet(worksheet, 'R2:R' + str(len(neutral_list) + 1), neutral_list.to_list())
    update_column_to_google_spreadsheet(worksheet, 'S2:S' + str(len(negative_list) + 1), negative_list.to_list())

def update_column_to_google_spreadsheet(worksheet, column_range, cell_value_list):
    cell_list = worksheet.range(column_range)
    for (index, cell) in enumerate(cell_list):
        cell.value = cell_value_list[index]
    worksheet.update_cells(cell_list)



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
    print("")
    print("analyze_sentiment_context")
    print("한꺼번에 구했을 때의 총 점수 : ")
    score, magnitude, doc_sentences = analyze_sentiment(feedback)
    print(str(len(doc_sentences)) + "개의 문장")
    print("")

    if len(doc_sentences) <= 0:
        return

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

    return score, magnitude, doc_sentences


# 띄어쓰기 검사기 돌려랏
# feedback = "무엇보다도 타격감이 엄청 좋은 거 같아요. 조작도 쉽고 하니까 누구나 재미있게 플레이를 할 수 있을 거 같아요. '태그액션' 이라는 장르가 사실 익숙한 장르가 아니다 보니까 조금은 이상했었는데 이렇게나 개성있는 게임을 플레이를 하니 정말 좋았습니다. RPG 게임이 정말 지루하다고 생각했습니다. 하지만 이렇게 스테이지 형식의 게임으로 플레이를 해보니 정말 재미있네요. 신박해서 정말 좋았습니다. 때리다보면 귀도 즐겁네요!"
# feedback = "첫 인상 ) UI가 너무 간단하다 못해 퀄리티가 떨어져보여요. 아무리 게임이 재밌다고 하더라도 UI보고 약간 꺼려할 거 같아요. 약간만 바꾸면 좋을 듯 합니다. 처음하는 사람은 이게 뭐지 싶을 거 같아요. 플레이 도중 ) 타격감도 좋고 게임 다 신기하고 뭔가 엄청 신박해서 좋은데 보스까지 처치하고 나서 메인 메뉴로 이동이 없어서 조금 아쉬워요! 그거 말고는 저는 다 좋았던 거 같아요. UI도 처음에는 왜 이렇게 놨을까 하고 고민을 조금 했는데 방치형이랑 스테이지 형식의 게임을 조금 섞어서 만든 거처럼 그래서 그랬던거구나 싶었습니다."
# feedback = '일단 제가 말씀 드릴 수 있는건 아주 조금뿐이라는 양해말씀 드립니다.'
# feedback = '개인적으로 조작감이 별로고 캐릭터의 움직임이 느리고 답답하다는 생각이 들었습니다. 하지만 게임자체는 다듬으면 재밌을 것 같았습니다.'
# feedback = '해당 장르 게임의 전통 같은 느낌이라 어쩔 수 없다고 봅니다.'
# analyze_sentiment_each_sentence(feedback)
# analyze_sentiment_context(feedback, False)
# filename="./feedback"
# load_workbook(filename, data_only=True)


spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1wxJdRDKc4HnsVlMxd41vnw2rb9AbVEkSHC3uomu6ISA'
worksheet = get_google_spread_sheet_workspace(spreadsheet_url)
feedback_dataframe = get_feedback_dataframe(worksheet,
                                            feedback_col_title='6. 게임의 유지할 점이나 아쉬웠던 점을 적어주세요.',
                                            email_col_title='* 자동 입력된 이메일 정보입니다.')
print(feedback_dataframe)

def writeResultToSpreadSheet(worksheet, feedback_dataframe):
    feedback_list = feedback_dataframe.loc[:, 'feedback'].to_list()

    for (index, feedback) in enumerate(feedback_list):
        score, magnitude, doc_sentences = analyze_sentiment_context(feedback, is_verbose=True)
        print(score)
        feedback_dataframe.at[index + 1, 'score'] = score
        feedback_dataframe.at[index + 1, 'magnitude'] = magnitude
        feedback_dataframe.at[index + 1, 'sentence_count'] = len(doc_sentences)
        feedback_dataframe.at[index + 1, 'feedback_length'] = len(feedback)

        negative_list = list(filter(lambda sen: sen.sentiment.score < 0, doc_sentences))
        neutral_list = list(filter(lambda sen: sen.sentiment.score == 0, doc_sentences))
        positive_list = list(filter(lambda sen: sen.sentiment.score > 0, doc_sentences))

        negative_list = list(map(lambda neg: str(neg.text.content), negative_list))
        neutral_list = list(map(lambda neg: str(neg.text.content), neutral_list))
        positive_list = list(map(lambda neg: str(neg.text.content), positive_list))

        feedback_dataframe.at[index + 1, 'negative_list'] = "\n".join(negative_list) if len(negative_list) > 0 else "-"
        feedback_dataframe.at[index + 1, 'neutral_list'] = "\n".join(neutral_list) if len(neutral_list) > 0 else "-"
        feedback_dataframe.at[index + 1, 'positive_list'] = "\n".join(positive_list) if len(positive_list) > 0 else "-"

        break

    print(feedback_dataframe)

    # 흠.. 이렇게하고보니 row가 더 나았을 수 있었겠다^^...
    update_score_to_google_spreadsheet(worksheet, feedback_dataframe.loc[:, 'score'])
    update_magnitude_to_google_spreadsheet(worksheet, feedback_dataframe.loc[:, 'magnitude'])
    update_sentence_count_to_google_spreadsheet(worksheet, feedback_dataframe.loc[:, 'sentence_count'])
    update_feedback_length_to_google_spreadsheet(worksheet, feedback_dataframe.loc[:, 'feedback_length'])
    update_each_sentence_scores_to_google_spreadsheet(worksheet,
                                                      positive_list=feedback_dataframe.loc[:, 'positive_list'],
                                                      negative_list=feedback_dataframe.loc[:, 'negative_list'],
                                                      neutral_list=feedback_dataframe.loc[:, 'neutral_list'])

def convertStyle(sentence):
    if sentence.sentiment.score > 0:
        return '<span style="color: #00BFBA;"><b>' + sentence.text.content + '</b></span>'
    elif sentence.sentiment.score < 0:
        return '<span style="color: #FF8997;"><b>' + sentence.text.content + '</b></span>'
    else:
        return sentence.text.content

def writeResultToHtml(feedback_dataframe):
    feedback_list = feedback_dataframe.loc[:, 'feedback'].to_list()
    email_list = feedback_dataframe.loc[:, 'email'].to_list()

    f = open("새파일.html", 'w')

    head = '총 피드백 개수 : ' + str(len(feedback_list))
    f.write(head)

    tableHead = '<table border="1">  ' \
           '<tr>' \
           '<th></th>' \
           '<th>Email</th>' \
           '<th>점수</th>' \
           '<th>피드백 길이</th>' \
           '<th>Feedback</th>' \
           '</tr>'

    f.write(tableHead)

    for (index, feedback) in enumerate(feedback_list):
        if len(feedback) <= 0: continue

        score, magnitude, doc_sentences = analyze_sentiment_context(feedback, is_verbose=True)
        print(score)
        feedback_dataframe.at[index + 1, 'score'] = score
        feedback_dataframe.at[index + 1, 'magnitude'] = magnitude
        feedback_dataframe.at[index + 1, 'sentence_count'] = len(doc_sentences)
        feedback_dataframe.at[index + 1, 'feedback_length'] = len(feedback)

        print(feedback_dataframe.loc[index+1, :])

        data = '<tr>'
        data += '<td>'
        data += str(index + 1)
        data += '</td>'
        data += '<td>'
        data += email_list[index]
        data += '</td>'
        data += '<td>'
        data += str(feedback_dataframe.loc[index+1, 'score'])
        data += '</td>'
        data += '<td>'
        data += str(feedback_dataframe.loc[index+1, 'feedback_length'])
        data += '</td>'
        data += '<td>'
        data += '<br>'.join(list(map(convertStyle, doc_sentences)))
        data += '</td>'
        data += '</tr>'
        print(data)
        f.write(data)

    f.write('</table>')
    f.close()

writeResultToHtml(feedback_dataframe)