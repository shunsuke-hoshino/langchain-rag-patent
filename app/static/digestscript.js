new Vue({
    el: '#processing',
    data: {
        productinfo: '',
        responseData: null,
    },
    computed: {
        renderedMarkdown() {
            return marked(this.responseData); // マークダウンをHTMLに変換
        }
    },
    methods: {
        fetchInfo() {
            fetch('/sendinfo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ productinfo: this.productinfo })
            })
            .then(response => response.json())
            .then(data => {
                this.responseData = data; // 受け取ったデータを格納
                console.log('Received data:', this.responseData); // デバッグ用
            })
            .catch(error => {
                console.error('Error:', error);
            });
        },
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
