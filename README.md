# 本研究の入力補完機能の状況
## 本研究の入力補完の状況
これまで，N-gram手法をベースとした予測手法を実装していました．
詳細は修士論文に記述していると思うので，簡潔に書きます．

### N-gram手法の簡単な説明
学習ファイルのトークンをN単位ごとに分割し，そのトークン列と出現数を記録します．
* 以下は学習用の例文
  * I am a teacher.
  * I am fine.
  * I play soccer.

上記の例文に対して，2トークンごとに分割した(N=2の)場合，以下のトークン列が得られます．

* 「I am」「am a」「a teacher」
* 「I am」「am fine」
* 「I play」「play soccer」

これらが得られたトークン列であり，同じパターンをカウントして記録します．
例えば今回の場合は「I am」が2回登場しています．<br>
得られたトークン列から，ユーザが「I」と入力した場合は「am」「play」などを提案でき，出現回数に応じて優先度を付与することなども可能になります．

以上が本研究で利用していたN-gramの基本的な説明です．

### 最初のN-gram手法
上記のN-gram手法で説明した方法をそのまま適用しました．
Mizarの字句解析器を用い，トークンを分割，トークン列の出現数と共にJSONファイルに保存を行いました．<br>
結果として，以下のような課題に直面しました．
* トークン列のパターンが膨大で，JSONにリストで保存するには限界がある（出現数順にソートし，閾値以下のトークン列を切り捨てることになりました）
* 変数名が異なるだけで，別パターンのトークン列として扱われてしまう
* 宣言していない変数を提案してしまう
* importしていないシンボルを提案してしまう
* JSONファイルを線形に検索していたため，スピードが遅い

上記の課題を解消するために前処理を行い，トライ木を用いた次のような手法を開発しました．

### 前処理・トライ木を用いたN-gram手法
* 学習用のファイルに出現するトークンをクラスに分類して，JSONファイルに保存する（例えばx,yなどの変数は「\_\_variable\_」にするなど）
* 環境部（プログラミングのimportに相当する部分）を解析し，ユーザが利用するシンボルのみを提案可能にするため，JSONファイルにシンボルのリストを種類ごとに保存する
* 検索スピード改善のために，クラス名をベースにしたトライ木を構築する

この手法によって，以下のような改良が実現できました．
* importしていないシンボルが提案されない
* 変数などの提案は，ユーザが宣言したもののみを記録しておき提案する
* 予測速度が向上した
* キーストローク数が入力補完機能を利用しない場合と比較して，21\%程削減された
* 予測精度が高まった（2文字目の入力を行った場合，3候補以内で8割，10候補以内で9割以上の正答率を示した）

また上記と比較するために前処理を行わず，トライ木のみを用いたN-gram手法も実装しました．（この辺りについては修士論文に詳しく書いていると思うので割愛します）

## 今後の課題（おそらく引き継いでいただく内容）
* ディープラーニングを用いた手法の開発
  * 0文字入力時が，前処理を行わない手法の方が精度が高かったため，クラス化によって予測に必要な情報が失われたと考えられます
* スペルミスを検知し，訂正案を出す機能の実装
* 実際に拡張機能に実装し，ユーザから意見・感想をいただくこと

## 入力補完の評価用プログラム
これらのプログラムはMMLに前処理を行ったJSONファイルを利用して，以下の評価を行うプログラムです．
* キーストロークの削減数の計測
* キーワードの予測精度の計測

予測モデルを引数として渡すことで，それぞれの計算を行います．
予測モデルは，以下の属性を持つことを想定しています．

* N-gramのNの値（ディープラーニングのモデルでは不要になると思います，評価プログラムでNを利用しているような部分があるため自由に修正してください）
* predictメソッド（必須）
  * 引数
    * user_input: ユーザカーソル直前のトークン列を，トークン単位で分割したリスト
    * parsed_input: ユーザカーソル直前のトークン列を，クラス単位で分割したリスト
      * トークンのクラス分け方法
        * 予約語：そのまま
        * 変数：\_\_variables\_
        * ラベル：\_\_labels\_
        * 数字：\_\_number\_
        * シンボル：以下の8種の内で該当するもの
          * \_\_R\_: Predicate
          * \_\_O\_: Functor
          * \_\_M\_: Mode
          * \_\_G\_: Structure
          * \_\_U\_: Selector
          * \_\_V\_: Attribute
          * \_\_K\_: Left Functor Bracket
          * \_\_L\_: Right Functor Bracket
    * type_to_symbols
      * vocabularies部でimportしているシンボル群<br>
      上記のシンボルクラスをキーとして，シンボル群がリストとして格納されている<br>
      JSONファイルの"symbols"部に相当
    * variables
      * ユーザが宣言した変数を保持するリスト<br>
      現状ではこのような実装になっていますが，新しい手法に合わせて自由に修正してください
    * labels
      * ユーザが宣言，引用したラベルを保持するリスト<br>
      変数と同様，新しい手法に合わせて自由に修正してください

* learningメソッド（モデルのメソッドとして実装するかの判断は委ねます）

評価プログラムは必要に応じて修正していただく必要があると思います．

## キーストローク削減数の計測プログラム(assess_keystroke.py)

```python
original_cost, reduced_cost, prediction_times = assess_mml_keystroke(model)
```

のように呼び出すことで，キーストロークの削減数を学習ファイル以外の256ファイルを用いてシミュレートします．

* original_cost: スペースと改行以外に必要なキーストローク数
* reduced_cost: 入力補完プログラムを用いた場合に削減できたキーストローク数
* prediction_times: 予測した回数

ユーザは入力数が減らせる場合に限り，入力補完機能を利用することを前提としています．
例えば「abcde」と入力したい場合，通常では5回のキー入力を必要とします．
もしユーザが「a」と入力した時点で，第一候補に「abcde」が提案された場合，ユーザはTabキーを入力すれば2回の入力で完了するため，3回のキー入力の削減が実現されます．<br>
もし「a」と入力した時点で第5候補に「abcde」が提案された場合は，下矢印キー4回とTabキーの入力が必要となり，通常の入力数より多くなってしまうため，ユーザは入力補完機能を利用しません．


## 予測精度の計測プログラム(assess_accuracy.py)
（デフォルトでは）10候補以内の予測の正答率を計測するプログラムです．
ユーザカーソル直前のトークン列を利用して予測を行います．
そのためユーザが何も入力していない場合（0文字入力時）から5文字目まで入力した場合など，それぞれの計測が行われます．
draw関数のコメントアウトを解除すれば，棒グラフの画像を出力することも可能です．

### 正答率の計算方法
予測精度を測る際，1000回の予測を行うファイルが存在するとします．
1000回全てに正解すれば，精度は100\%となるため，ユーザの入力が0文字の場合，分母は1000と設定できます．
よって，第1候補で200回正解すれば，0文字入力時の第1候補の正答率は20\%となります．<br>
次にユーザが1文字目を入力した場合を考えます．
ユーザは1文字目の入力を完了しているため，予測プログラムは2文字以上のキーワードを推測して提案します．
この時点で1文字以下のキーワードは予測対象外のため，分母から1文字以下のキーワード数を除く必要があります．
よって分母はファイル内に出現する2文字以上のキーワード数になります．
例えば先ほどのファイルで，400個のキーワードが1文字だった場合，1文字入力時の正答率に利用する分母は600となります．<br>
2文字目以降も同様に分母から対象外のキーワードを除いていきます．

以上が実装されている正答率の計算方法です．

## trie_ngram_modelの評価方法の例
trie_ngram_model.pyのメイン関数では，以下のような処理を行っています．
実行方法は上で説明した通りで，assess_mml_accuracy関数やassess_mml_keystroke関数に開発したモデルを渡します．
これらの関数では，modelの持つpredictメソッドを実行しているため，注意してください．

```python
if __name__ == "__main__":
    from assess_keystroke import assess_mml_keystroke
    from assess_accuracy import assess_mml_accuracy
    trie_model = TrieNgramModel()
    # np.set_printoptions(precision=1)
    # assess_mml_accuracy(trie_model)
    original_cost, reduced_cost, prediction_times = assess_mml_keystroke(trie_model)
    print(original_cost, reduced_cost, prediction_times)
    del os.environ["PROJECT_DIR"]
```

