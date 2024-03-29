import json
import os
from collections import OrderedDict, deque

# Tab,矢印キーなどのコストを設定する変数
SPECIAL_KEY_COST = 1
PROJECT_DIR = os.environ["PROJECT_DIR"]


def get_user_input(N, i, line_tokens, parsed_tokens):
    if i >= N:
        user_input_list = line_tokens[i - N + 1 : i]
        parsed_input_list = parsed_tokens[i - N + 1 : i]
    else:
        user_input_list = line_tokens[:i]
        parsed_input_list = parsed_tokens[:i]

    return user_input_list, parsed_input_list


def file_name_to_absolute(file_name):
    return f"{PROJECT_DIR}/learning_data/" + file_name


def assess_file_keystroke(file_name, model):
    # NOTE:modelにNを持たせておく
    N = model.N
    file_name = file_name_to_absolute(file_name)
    with open(file_name, "r") as f:
        json_loaded = json.load(f)
    type_to_symbols = json_loaded["symbols"]
    article = json_loaded["contents"]
    variables = []
    labels = []
    original_cost = 0
    cost_with_completion = 0
    reduced_cost = 0
    prediction_times = 0
    # lineは[[let, let], [x, __variable_], [be, be], [object, __M_]]のような形式
    for line in article:
        line_tokens = []
        parsed_tokens = []
        # print(f'original_cost:{original_cost}, cost:{cost}')
        for token in line:
            # tokenは["x", "__variable_"]のようになっている
            line_tokens.append(token[0])
            parsed_tokens.append(token[1])
        length = len(line)
        # 文頭のトークンは予測できないため，コストとして追加
        first_token_cost = len(line_tokens[0])
        original_cost += first_token_cost
        cost_with_completion += first_token_cost
        prediction_times += 1
        for idx in range(1, length):
            prediction_times += 1
            answer = line[idx][0]
            remaining_cost = len(answer)
            original_cost += remaining_cost
            user_input, parsed_input = get_user_input(
                N, idx, line_tokens, parsed_tokens
            )
            # suggested_keywordsは{キーワード:提案順位}の形式
            # 例：{"be":1, "being":2}
            suggested_keywords = model.predict(
                user_input, parsed_input, type_to_symbols, variables, labels
            )
            # 残りの入力に必要なコストが特殊キーのコスト以下ならコスト削減の可能性はない
            if remaining_cost <= SPECIAL_KEY_COST:
                cost_with_completion += remaining_cost
            elif answer in suggested_keywords:
                input_idx = 0
                # 残りの入力コストが特殊キーのコストより大きい場合，コスト削減の可能性がある
                while remaining_cost > SPECIAL_KEY_COST:
                    select_cost = SPECIAL_KEY_COST * suggested_keywords[answer]
                    if select_cost < remaining_cost:
                        reduced_cost += remaining_cost - select_cost
                        cost_with_completion += select_cost
                        break
                    # 1文字入力して，提案キーワードを更新する処理
                    else:
                        input_idx += 1
                        cost_with_completion += 1
                        # 1文字入力したため，トークンを入力するコストが「1」減少する
                        remaining_cost -= 1
                        # 残りのコストが2未満の場合は，節約にならないため，残りのコストを加えて終了
                        if remaining_cost <= SPECIAL_KEY_COST:
                            cost_with_completion += remaining_cost
                            break
                        # 提案キーワード群の更新
                        tmp = deque()
                        for keyword in suggested_keywords:
                            if keyword.startswith(answer[:input_idx]):
                                tmp.append(keyword)
                        suggested_keywords = OrderedDict({})
                        # 提案キーワードの順位を保持する変数
                        cnt = 1
                        for keyword in tmp:
                            suggested_keywords[keyword] = len(suggested_keywords) + 1
                            cnt += 1
            else:
                cost_with_completion += remaining_cost
    return original_cost, reduced_cost, prediction_times


def assess_mml_keystroke(model):
    original_cost, reduced_cost, prediction_times = 0, 0, 0
    mml_lar = open(f"{PROJECT_DIR}/about_mml/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(i.replace("\n", ".json"))
    mml_lar.close()
    # NOTE:mml.larの順番で評価に利用するファイル
    for file_path in mml[1100:1356]:
        print(file_path)
        try:
            (
                file_original_cost,
                file_reduced_cost,
                file_prediction_times,
            ) = assess_file_keystroke(file_path, model)
            original_cost += file_original_cost
            reduced_cost += file_reduced_cost
            prediction_times += file_prediction_times

        except Exception as e:
            print(e)
            continue
        print(
            original_cost,
            reduced_cost,
            reduced_cost / original_cost * 100,
            prediction_times,
        )
    return original_cost, reduced_cost, prediction_times
