import os
from flask import Flask, request, render_template, jsonify, send_file,Response
from openai import OpenAI
from dotenv import load_dotenv
import requests
import csv
import io
from werkzeug.utils import secure_filename
from langchain_community.vectorstores import Vectara
from langchain_community.vectorstores.vectara import (
    RerankConfig,
    SummaryConfig,
    VectaraQueryConfig,
)
import re
import time


#if 'WEBSITE_HOSTNAME' not in os.environ:
load_dotenv(override=True)
vectara_customer_id = os.getenv("VECTARA_CUSTOMER_ID")
vectara_corpus_id = os.getenv("VECTARA_CORPUS_ID")
vectara_api_key = os.getenv("VECTARA_API_KEY")

vectara = Vectara(
    vectara_customer_id=vectara_customer_id,
    vectara_corpus_id=vectara_corpus_id,
    vectara_api_key=vectara_api_key
)

summary_config = SummaryConfig(is_enabled=True, max_results=7, response_lang="ja")
rerank_config = RerankConfig(reranker="mmr", rerank_k=50, mmr_diversity_bias=0.2)
config = VectaraQueryConfig(
    k=10, lambda_val=0.005, rerank_config=rerank_config, summary_config=summary_config
)

config.summary_config.is_enabled = False
config.k = 3
retriever = vectara.as_retriever(config=config)

#openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)
ai_model = "gpt-4o-mini"

def chat_with_ai(template, message):
    response = client.chat.completions.create(
        model=ai_model,  # または他の適切なモデルを選択
        messages=[
            {"role": "system", "content": template},
            {"role": "user", "content": message}
        ]
    )
    print(response.usage.prompt_tokens)
    return response.choices[0].message.content

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/digest.html")
def digest():
    return render_template("digest.html")

@app.route("/idea_generate.html")
def idea():
    return render_template("idea_generate.html")

@app.route('/generate_formula', methods=['POST'])
# ここで論理式を生成するロジックを実装

def generate_logic_expression():
    data = request.get_json()
    product_name = data.get('productName')
    keywords = data.get('keywords')
    number = data.get('number')
    
    template = "あなたは特許調査のプロフェッショナルであり、特許検索の式だけを答えます。\n論理式はORを+と表示し、ANDを*と表示してください。\n類似語は+で繋げるようにしてください。それ以外は*で繋げてください。\nまた次のように「火傷+やけど+火傷予防+やけど防止」という結果だと結果(火傷・やけど)と対策(火傷予防・やけど防止)が論理式で一緒になっています。そのような場合は原因・結果・対策を分けたうえで*でつないで表記してください。\n論理式の形の例を与えます。\n(商品名類義語+商品名類義語+商品名類義語) * (キーワード類義語+キーワード類義語+キーワード類義語)...etc\n具体的な例としてはキーワード：「絡まる」だった場合、絡み、挟ま、巻き付、キーワード：「予防」だった場合、防ぐ、阻止といったものも論理式に含んでください。\n上記はあくまでも具体例です。\n類義語でも「~する」といった言葉をつけたものは省いてください。例: 予防+予防する+防止+防ぐ→予防+防止+防ぐ\nあなたなら出来る"
    prompt = f"商品名: {product_name}\nキーワード: {keywords}\nこれらに基づいて特許調査の論理式を生成してください。{product_name}と{keywords}から特許課題を類推し、論理式に含めてください。\n{product_name}の類義語、似ているものを出来るだけ多く調べ、論理式に含めてください。{keywords}の類似語は{number}の数だけ調べ、論理式に含めてください。\n日本語と記号だけで構成してください"
    #print("OpenAI API response: ", completion.choices[0].message.content) # レスポンスから内容のみを取得
    edit = chat_with_ai(template, prompt)
    #print(edit)
    #print(completion.usage)
    editdata = []
    editdata = edit.split('*')
    #print("edi:",editdata)
    #print(editdata[0])
    cleaned_data = editdata[0].strip('(')  # 括弧を取り除く
    result_list = cleaned_data[0:len(cleaned_data)-2].split('+')  # +で区切る
    #print("result_list",result_list)

    page_contents_list = []  # 各レスポンスを格納するリスト
    for item in result_list:
        response = retriever.invoke(item)  # 各アイテムに対してinvokeを呼び出す
        page_contents = [doc.page_content for doc in response]  # ページコンテンツを取得
        page_contents_list.append(page_contents)  # 結果をリストに追加
        
    print(page_contents_list)
        
    template2 = "あなたは特許調査のプロフェッショナルであり、国際特許分類（IPC）を細分化した日本国特許庁独自の特許文献の分類であるFIだけを答えます。わからない場合は「 」を出力してください。\n"
    prompt2 = f"FI情報{page_contents_list}\n商品名{product_name}\nに基づいて特許調査のFI記号のみを出力してください。関係がありそうだと考えたFI記号は+の文字でつなげて含めてください。5つ程度出力してください。半角スペースなどは含めないでください。ただし、私が与えた全ての内容のみに基づいて、それ以外の情報を創造してはいけません。\n日本語と記号だけで構成してください"
    result_fi=chat_with_ai(template2, prompt2)
    #print("結果",result_fi)
    
    tempdata = [data.replace('(', '').replace(')', '') for data in editdata]

    editdata.clear()
    editdata.extend(tempdata)

    editdata = [data.replace(' ', '') for data in editdata]
    #print(editdata)

    data_rows = []
    with open('app/static/formula.tsv', mode='w', newline='', encoding='Shift-JIS') as fo:
    
        tsv_writer = csv.writer(fo, delimiter='\t')
        tsv_writer.writerow(['検索データベース', '国内特許'])
        tsv_writer.writerow(['式No.', '登録件数', '検索項目', '条　件　式'])
                
        for i in range(len(editdata)):
            data_rows.append(['S00' + str(i + 1), '', '全文', editdata[i]])

        appenddata = ['S00' + str(len(editdata) + 1), '', '論理式', '*'.join(['S00' + str(i) for i in range(1, len(editdata) + 1)])]
        data_rows.append(appenddata)
        
        for row in data_rows:
            try:
                tsv_writer.writerow(row)
            except Exception as e:
                print(f"エラーが発生しました: {e}")
    #tempdata = [data.replace('(', '').replace(')', '') for data in editdata]
    edi_logic = edit.replace('(', '').replace(')', '')
    e = edi_logic.replace(' ', '')
    logic_expression = []
    logic_expression = e.split('*')
    rtn = " " in result_fi
    logic_expression.append(result_fi)
    #print(logic_expression)

    #logic_expression = completion.choices[0].message.content

    # logic_expression = fetch_logic_expression(product_name, keywords)
    

    # logic_expression = f"({product_name} AND {keywords})"
    return jsonify(logic_expression)

@app.route('/download_formula', methods=['POST'])
def download_formula():
    data = request.get_json()
    data_rows = []
    print(data)
    edited_formula = data.get('editedFormula')
    search_item = data.get('searchItems')
    
    # print("edited_formula=",edited_formula)
    # print("search_item=",search_item)
    # print(data['searchItem'])
    # ファイルパスを設定
    file_path = os.path.join('static', 'formula.tsv')

    # ファイルに書き込み
    # with open('app/static/formula.tsv', 'w', encoding='Shift-JIS') as f:
    #     f.write(f"検索項目: {search_item}\n")
    #     f.write(f"論理式: {edited_formula}\n")

    edit = []
    edit = edited_formula
    editdata = edit.split('.')
    #print("edi:",editdata)
    tempdata = [data.replace('(', '').replace(')', '') for data in editdata]

    editdata.clear()
    editdata.extend(tempdata)

    editdata = [data.replace(' ', '') for data in editdata]
    
    with open('app/static/formula.tsv', mode='w', newline='', encoding='Shift-JIS') as fo:
        tsv_writer = csv.writer(fo, delimiter='\t')
        tsv_writer.writerow(['検索データベース', '国内特許'])
        tsv_writer.writerow(['式No.', '登録件数', '検索項目', '条　件　式'])
        
        for i in range(len(editdata)):
            data_rows.append(['S00' + str(i + 1), '', search_item[i], editdata[i]])

        appenddata = ['S00' + str(len(editdata) + 1), '', '論理式', '*'.join(['S00' + str(i) for i in range(1, len(editdata) + 1)])]
        data_rows.append(appenddata)
        
        for row in data_rows:
            tsv_writer.writerow(row)
    
    # ファイルのURLを返す
    return jsonify({'file_url': f'/{file_path}'})

@app.route('/stream_response', methods=['POST'])
def stream_response():
    data = request.get_json()
    productinfo = data.get('productinfo')
    buffer = ""  # バッファを初期化

    def generate_stream():
        nonlocal buffer
        for new_content in openai_stream_function(productinfo):  # OpenAIのストリーミング関数を呼び出す
            buffer += new_content  # バッファに追加
            buffer = buffer.replace(' ', '')
            # 完全なタグを探して送信
            while True:
                # バッファ内の完全なタグを探す
                match = re.search(r'(<[^>]+>.*?</[^>]+>)', buffer)
                if match:
                    chunk = match.group(0)
                    yield f"data: {chunk}\n\n"  # 完全なタグを送信
                    buffer = buffer.replace(chunk, '', 1)  # 送信した部分をバッファから削除
                else:
                    break

        # 残りのバッファがあれば送信
        if buffer:
            yield f"data: {buffer}\n\n"

    return Response(generate_stream(), content_type='text/event-stream')

# OpenAIのストリーミング関数
def openai_stream_function(productinfo):
    prompt = f"{productinfo}\nこの特許の内容を、わかりやすく詳しく解説してください。ただし、私が与えた全ての内容のみに基づいて、それ以外の情報を創造してはいけません。意見や推測も避けてください。情報が正確かどうか二度確認してから出力をしてください。またこの特許文書が示す特許にある、【弱点や課題】があれば指摘してください。また、他事業者によってこの特許が【特許回避される懸念箇所】があれば指摘してください。日本語だけで回答してください。"
    template = """あなたは特許調査のプロフェッショナルであり、特許の要約を答えます。HTML形式で答えてください。```htmlといった表記はいりません。\n
    回答の際は以下の点に注意してください：\n
    1. 特許の新規性、進歩性、産業上の利用可能性を分析し、具体的な根拠を示してください。\n
    2. 類似特許や関連技術との比較を行い、対象特許の技術的特徴や優位性を明確に説明してください。\n
    3. 類似特許について言及するときは、具体的な特許番号や引用元を示してください。具体的な特許番号が不明な場合は、その情報を使用しないでください。\n
    4. 特許請求項の範囲と明細書の記載内容を精査し、権利範囲の解釈について言及してください。\n
    5. 技術分野、IPC（国際特許分類）、FI、Fタームなどの分類情報を提供し、技術領域を特定してください。\n
    6. 先行技術文献や引用文献の重要性を評価し、対象特許との関連性を説明してください。\n
    7. 特許戦略や権利化の可能性について、市場動向や技術トレンドを考慮した見解を提供してください。\n
    8. 専門用語を使用する際は、理解しやすい説明を付け加え、必要に応じて具体例を示してください。\n
    9. 法的助言に相当する内容は避け、複雑な法的問題については弁理士や弁護士への相談を推奨してください。\n
    10. 検索結果の網羅性、信頼性、最新性について評価し、情報の限界や不確実性にも言及してください。\n
    11. 特許の法的状況（審査中、登録済、無効、満了など）、権利の有効期限、年金納付状況などを確認し、報告してください。\n
    12. 複数の関連特許文献がある場合、技術的特徴や権利範囲の比較表を作成し、分かりやすく提示してください。\n
    13. 国際出願（PCT）の状況、主要国での権利化状況、ファミリー特許の情報を提供し、グローバルな権利状況を説明してください。\n
    14. 対象特許の価値評価や活用可能性について、技術的・経済的観点から考察を加えてください。\n
    15. 非特許文献（学術論文、技術標準など）との関連性があれば指摘し、技術の背景や発展状況を補足してください。\n
    回答は必ず日本語で行い、論理的かつ具体的に説明してください。情報の解釈には不確実性が伴うことを明記し、専門家による追加の分析や確認を推奨してください。また、検索・分析の制約や限界についても適切に言及してください。"
    
    最終的な回答は日本語で以下{# 出力形式}に従ったものとすること。
    
    # 出力形式
    <h1>特許概要解説-{特許の発明の名称}{公開番号}</h1>
    <h2>発明の背景と目的：</h2>
    <p>{この特許の発明の背景と目的}</p>

    <h2>発明の技術的特徴：</h2>
    <p>{この特許の技術的特徴に関する記述}</p>

    <h2>特許請求項の要点：</h2>
    <ul>
    <li>{請求項1：}</li>
    <li>{請求項2：}</li>
    <li>{一つ一つの特許請求項に関する記述：}</li>
    </ul>
    <p>{請求項に対するまとめ}</p>

    <h2>課題と弱点：</h2>
    <p>{この特許の課題や弱点に関する記述}</p>
    <h2>特許回避される懸念箇所：</h2>
    <p>{この特許の特許回避される懸念箇所に関する記述}</p>
    <h2>結論：</h2>
    <p>{この特許に関する結論に関する記述}</p>
    """

    stream = client.chat.completions.create(
        model=ai_model,
        messages=[
            {"role": "system", "content": template},
            {"role": "user", "content": prompt}
        ],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            #print(chunk.choices[0].delta.content, end="")
            yield chunk.choices[0].delta.content  # ストリーミングされたコンテンツを返す
    
# Flaskのルートにファイルを受け取るエンドポイントを作成 
# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return 'No file part'
#     file = request.files['file']
#     if file.filename == '':
#         return 'No selected file'
#     if file:
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         return 'File uploaded successfully'

if __name__ == '__main__':
    app.run(debug=True)