import os
from flask import Flask, request, render_template, jsonify, send_file
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

def chat_with_ai(template, message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # または他の適切なモデルを選択
        messages=[
            {"role": "system", "content": template},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/digest.html")
def digest():
    return render_template("digest.html")

@app.route('/generate_formula', methods=['POST'])
# ここで論理式を生成するロジックを実装

def generate_logic_expression():
    
    ai_model = "gpt-4o-mini"
    data = request.get_json()
    product_name = data.get('productName')
    keywords = data.get('keywords')
    number = data.get('number')
    response = retriever.invoke(product_name)
    page_contents = [doc.page_content for doc in response]
    
    #また国際特許分類（IPC）を細分化した日本国特許庁 独自の 特許 文献の分類であるFIを*でつないで論理式に含めてください。ただし、私が与えた全ての内容のみに基づいて、それ以外の情報を創造してはいけません。上記FI表です。{fi}
    # {product_name}からIPC、FI、Fタームを*でつないで論理式に含めてください。IPC、FI、Fタームは情報が正確かどうかわからない場合は含めないでください。含めない場合はIPC情報といった文言はいりません。
    #print(number)
    template = "あなたは特許調査のプロフェッショナルであり、国際特許分類（IPC）を細分化した日本国特許庁独自の特許文献の分類であるFIだけを答えます。わからない場合は「 」を出力してください。\n"
    prompt = f"FI情報{page_contents}\n商品名{product_name}に基づいて特許調査のFIを出力してください。関係がありそうだと考えたFI記号は+の文字でつなげて含めてください。半角スペースなどは含めないでください。ただし、私が与えた全ての内容のみに基づいて、それ以外の情報を創造してはいけません。\n日本語と記号だけで構成してください"
    result_fi=chat_with_ai(template, prompt)
    print(result_fi)
    template2 = "あなたは特許調査のプロフェッショナルであり、特許検索の式だけを答えます。\n論理式はORを+と表示し、ANDを*と表示してください。\n類似語は+で繋げるようにしてください。それ以外は*で繋げてください。\nまた次のように「火傷+やけど+火傷予防+やけど防止」という結果だと結果(火傷・やけど)と対策(火傷予防・やけど防止)が論理式で一緒になっています。そのような場合は原因・結果・対策を分けたうえで*でつないで表記してください。\n論理式の形の例を与えます。\n(商品名類義語+商品名類義語+商品名類義語) * (キーワード類義語+キーワード類義語+キーワード類義語)...etc\n具体的な例としてはキーワード：「絡まる」だった場合、絡み、挟ま、巻き付、キーワード：「予防」だった場合、防ぐ、阻止といったものも論理式に含んでください。\n上記はあくまでも具体例です。\n類義語でも「~する」といった言葉をつけたものは省いてください。例: 予防+予防する+防止+防ぐ→予防+防止+防ぐ\nあなたなら出来る"
    prompt2 = f"商品名: {product_name}\nキーワード: {keywords}\nこれらに基づいて特許調査の論理式を生成してください。{product_name}と{keywords}から特許課題を類推し、論理式に含めてください。\n{product_name}と{keywords}の類似語を{number}の数だけ調べ、論理式に含めてください。\n日本語と記号だけで構成してください"
    #print("OpenAI API response: ", completion.choices[0].message.content) # レスポンスから内容のみを取得
    
    edit = chat_with_ai(template2, prompt2)
    print(edit)
    #print(completion.usage)
    editdata = []
    editdata = edit.split('*')
    #print("edi:",editdata)
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
    if rtn == False:
        logic_expression.append(result_fi)
    print(logic_expression)

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



@app.route('/sendinfo', methods=['POST'])
def sendinfo():
    def extract_publication_number(text):
        # 正規表現を使用して【公開番号】を抽出
        match = re.search(r'【公開番号】(.*?)\s', text)
        if match:
            return match.group(1)  # マッチした部分を返す
        return None  # マッチしなかった場合はNoneを返す

    

        
    ai_model = "gpt-4o-mini"
    info = request.get_json()
    productinfo = info.get('productinfo') # この中身(infoの中のproductinfoはdigest.htmlのv-model=productinfoに基づいて決まっている。)
    # 発明の名称を抽出
    # s1 = re.search(r'【発明の名称】(.*?)\s', productinfo)
    # # 【FI】を抽出
    # fi_match = re.search(r'【ＦＩ】\s*(.*?)\s*【', productinfo)
    # fi_info = fi_match.group(1) if fi_match else None  # マッチした部分を取得

    # print("s1:",s1)
    # print("s2:",fi_info)
    # # FI表.txtに発明の名称とFIを追加予定 joinならできるかも
    # fstr = open('app/FI表.txt', 'r', encoding='UTF-8')
    # fs = fstr.read()
    # print(type(fs))
    # fs.append(s1 + ":" + fi_info)
    # print(fs)

    #print(info)
    #print(productinfo)
    publication_number = extract_publication_number(productinfo)
    #print(publication_number)
    # ファイルに書き込む
    file_path = f"./app/patedata/{publication_number}.md"  # 公開番号をファイル名に使用
    #file_path = "./app/patedata/output.md"  # ファイルのパスと名前を指定してください
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(productinfo)
    
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
    """
    completion = client.chat.completions.create(
        model=ai_model,
        messages=[
            {"role": "system", "content": template},
            {"role": "user", "content": prompt},
        ]
    )

    processed_data = completion.choices[0].message.content
    print(processed_data)
    return jsonify(processed_data)
    
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