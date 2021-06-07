edit_button = document.getElementById("edit_button")
back_button = document.getElementById("back_button")
mylist = document.getElementById("mylist"); // マイリスト
mylist_delete = document.getElementById("select_mylist_delete") // マイリストから削除

// デフォルト非表示
back_button.style.display = "none"; // 最初は「戻る」ボタンは非表示
mylist_delete.style.display = "none"; // 最初は選択部分は非表示

// 「選択」ボタン, 「編集」ボタンが押されたとき
function edit() {
  edit_button.style.display = "none"; // 「編集」ボタンを非表示にする
  back_button.style.display = "block"; // 「戻る」ボタンを表示する
  mylist.style.display = "none"; // マイリストを非表示にする
  mylist_delete.style.display = "block"; // 選択部分を表示する
}

// 「戻す」ボタンが押されたとき
function back() {
  edit_button.style.display = "block"; // 「編集」ボタンを表示する
  back_button.style.display = "none"; // 「戻る」ボタンを非表示にする
  mylist.style.display = "block"; // 選択部分を表示する
  mylist_delete.style.display = "none"; // 検索結果を非表示にする
}