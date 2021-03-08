search = document.getElementById("search"); // 検索結果
select = document.getElementById("select_video"); // 選択部分

// デフォルト非表示
select.style.display = "none"; // 最初は選択部分は非表示

// 「選択」ボタンが押されたとき
function clickBtn1() {
    search.style.display = "none"; // 検索結果を非表示にする
    select.style.display = "block"; // 選択部分を表示する
}

// 「戻す」ボタンが押されたとき
function clickBtn2() {
    select.style.display = "none"; // 選択部分を非表示にする
    search.style.display = "block"; // マイリストを表示する
}