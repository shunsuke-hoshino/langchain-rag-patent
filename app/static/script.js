new Vue({
    el: '#app',
    data: {
        productName: '',
        keywords: '',
        result: '',  // ここにユーザーが編集した論理式が入ります
        number: '',
        searchItems: []  // ここにユーザーが選択した検索項目が入ります
    },
    computed: {
        splitResult() {
            return this.result.split('.');
        },
    },
    watch: {
        splitResult(newVal) {
            // splitResultが変更されたときにsearchItemsの長さを調整
            if (newVal.length > this.searchItems.length) {
                this.searchItems.push(...Array(newVal.length - this.searchItems.length).fill('全文'));
            } else if (newVal.length < this.searchItems.length) {
                this.searchItems.splice(newVal.length);
            }
        }
    },
    methods: {
        generateFormula() {
            // フォームデータをサーバーに送信して論理式を生成
            fetch('/generate_formula', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    productName: this.productName,
                    keywords: this.keywords,
                    number: this.number
                })
            })
            .then(response => response.json())
            .then(data => {
                this.result = data.join('.');
                this.searchItems = Array(this.splitResult.length).fill('全文');  // 初期値を設定
                this.searchItems[this.searchItems.length - 1] = 'FI';  // 最後の項目を「FI」に設定
                //this.searchItems.slice(-1)[0].fill('FI')
            })
            .catch(error => {
                console.error('Error:', error);
            });
        },
        copySingleFormula(index) {
            const formula = this.splitResult[index];
            navigator.clipboard.writeText(formula);  // アラートを削除
        },
        // copySingleFormula(index) {
        //     const formula = this.splitResult[index];
        //     navigator.clipboard.writeText(formula).then(() => {
        //         alert('コピーしました');
        //     }, () => {
        //         alert('コピーに失敗しました');
        //     });
        // },
        downloadFormula() {
            // 編集された論理式と検索項目をサーバーに送信してファイルをダウンロード
            fetch('/download_formula', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    editedFormula: this.result,
                    searchItems: this.searchItems
                })
            })
            .then(response => response.json())
            .then(data => {
                const url = data.file_url;
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'formula.tsv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        },
        updateResult() {
            this.result = this.splitResult.join('.');
        },
        add() {
            this.splitResult.push('');
            this.searchItems.push('全文');
            this.updateResult();
        },
        del(index) {
            this.splitResult.splice(index, 1);
            this.searchItems.splice(index, 1);
            this.updateResult();
        },
    }
});