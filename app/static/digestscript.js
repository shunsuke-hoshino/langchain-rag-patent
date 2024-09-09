new Vue({
    el: '#processing',
    data: {
        productinfo: '',
        responseData: '',
        answer: '',  // answerをデータプロパティとして追加
        askResponse: {},  // askResponseをデータプロパティとして追加
        answers: [],  // answersをデータプロパティとして追加
        question: ''  // questionをデータプロパティとして追加
    },
    computed: {
        renderedMarkdown() {
            return marked(this.responseData); // マークダウンをHTMLに変換
        }
    },
    methods: {
        updateState(newContent) {
            return new Promise(resolve => {
                setTimeout(() => {
                    this.answer += newContent;  // answerを更新
                    const latestResponse = {
                        ...this.askResponse,
                        choices: [{ ...this.askResponse.choices[0], message: { content: this.answer, role: this.askResponse.choices[0].message.role } }]
                    };
                    this.answers.push([this.question, latestResponse]);  // answersを更新
                    resolve(null);
                }, 33);
            });
        },
        fetchInfo() {
            fetch('/stream_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ productinfo: this.productinfo })
            })
            .then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let result = '';

                const readStream = () => {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            this.responseData = result;  // 最終的な応答を設定
                            return;
                        }
                        
                        const chunk = decoder.decode(value, { stream: true });
                        const cleanedChunk = chunk.replace(/^data: /gm, '');
                        result += cleanedChunk;  // 結果に追加
                        
                        // responseDataを更新
                        //this.responseData = result;  // ここで表示を更新
                        this.responseData = result;  // ここで表示を更新
                        this.updateState(cleanedChunk);  // ストリーミング中の応答を更新
                        readStream();  // 次のチャンクを読み込む
                    });
                };

                readStream();  // ストリーミングを開始
            });
        }
    }
});
// new Vue({
//     el: '#processing',
//     data: {
//         pdfFiles: [],
//         processedResult: ''
//     },
//     methods: {
//         handleDrop(event) {
//             event.preventDefault();
//             const files = event.dataTransfer.files;
//             for (let i = 0; i < files.length; i++) {
//                 this.pdfFiles.push(URL.createObjectURL(files[i]));
//             }
//         },
//         // ファイルアップロード時にpdfファイルを表示する処理
//         handleFileSelect(event) {
//             const files = event.target.files;
//             for (let i = 0; i < files.length; i++) {
//                 const file = files[i];
//                 if (file.type === 'application/pdf') {
//                     const reader = new FileReader();
//                     reader.onload = (e) => {
//                         // PDFファイルを表示
//                         const pdfObject = document.createElement('object');
//                         pdfObject.data = e.target.result;
//                         pdfObject.type = 'application/pdf';
//                         pdfObject.width = '100%';
//                         pdfObject.height = '500';
//                         document.getElementById('pdf-preview').appendChild(pdfObject);
//                     };
//                     reader.readAsDataURL(file);
//                 } else {
//                     alert('PDFファイルを選択してください');
//                 }
//             }
//         },
//         // ファイルアップロード時にpdfファイルをバックエンドに送信する処理
//         handleFileSelect(event) {
//             const file = event.target.files[0];
//             const formData = new FormData();
//             formData.append('file', file);

//             // バックエンドにファイルを送信
//             fetch('/upload', {
//                 method: 'POST',
//                 body: formData
//             })
//             .then(response => response.text())
//             .then(data => {
//                 console.log(data); // バックエンドからのレスポンスを出力
//             })
//             .catch(error => {
//                 console.error('Error:', error);
//             });
//         },
//     }
// });
