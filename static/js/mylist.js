mylist = document.getElementById("mylist"); // マイリスト
mylist_delete = document.getElementById("select_mylist_delete") // マイリストから削除

// デフォルト非表示
mylist_delete.style.display = "none"; // 最初は選択部分は非表示

// 「選択」ボタンが押されたとき
function clickBtn3() {
    mylist.style.display = "none"; // マイリストを非表示にする
    mylist_delete.style.display = "block"; // 選択部分を表示する
}

// 「戻す」ボタンが押されたとき
function clickBtn4() {
    mylist_delete.style.display = "none"; // 検索結果を非表示にする
    mylist.style.display = "block"; // 選択部分を表示する
}