import preprocess
import os
import re
import glob, json

RESERVED_WORDS = set(['according','aggregate','all','and','antonym','are','as',
  'associativity','assume','asymmetry','attr','be','begin','being','by',
  'canceled','case','cases','cluster','coherence','commutativity',
  'compatibility','connectedness','consider','consistency','constructors',
  'contradiction','correctness','def','deffunc','define','definition',
  'definitions','defpred','do','does','end','environ','equals','ex','exactly',
  'existence','for','from','func','given','hence','hereby','holds',
  'idempotence','identify','if','iff','implies','involutiveness',
  'irreflexivity','is','it','let','means','mode','non','not','notation',
  'notations','now','of','or','otherwise','over','per','pred','prefix',
  'projectivity','proof','provided','qua','reconsider','reduce','reducibility',
  'redefine','reflexivity','registration','registrations','requirements',
  'reserve','sch','scheme','schemes','section','selector','set','sethood','st',
  'struct','such','suppose','symmetry','synonym','take','that','the','then',
  'theorem','theorems','thesis','thus','to','transitivity','uniqueness',
  'vocabularies','when','where','with','wrt'])

SPECIAL_SYMBOLS = set([',', ';', ':', '(', ')', '[', ']', '{', '}', '=', '&',
    '->', '.=', '$1', '$2', '$3','$4','$5','$6','$7','$8','$9', '(#', '#)',
    '...', '$10'])

DATA_DIR = 'data'
MML_VCT = os.path.join('.', DATA_DIR, 'mml.vct')

MML_DIR = '/mnt/c/mizar/mml'
data = {}

N = 2

# 変数かどうかを判定する関数
def is_variable(line,idx):
    token = line[idx]
    matched = re.match(r'__\w+_', token)
    # NOTE:ラベルではないかの確認も必要
    if matched:
        return False
    elif idx+1 <= len(line)-1 and line[idx+1] == ':':
        return False
    elif 'by' in set(line[:idx]):
        return False
    elif 'from' in set(line[:idx]):
        return False
    else:
        return not token in reserved_words


def create_variable_history():
    import xml.etree.ElementTree as ET
    import copy

    tree = ET.parse('ring_1.xml')
    root = tree.getroot()
    d = {}
    variable_histroy = []

    for qv in root.iter('qualifiedVariables'):
        tmp_v = []
        tmp_mode = ''

        for v in qv.iter('variableIdentifier'):
            # print(f'variables:{v.attrib}')
            tmp_v.append(v.attrib['spelling'])
        
        for mode in qv.iter('modeSymbol'):
            # print(f'mode:{mode.attrib}')
            if 'spelling' in mode.attrib:
                tmp_mode = mode.attrib['spelling']
            else:
                tmp_mode = 'set'
        
        for v in tmp_v:
            d[v] = tmp_mode
        
        d_copy = copy.copy(d)
        variable_histroy.append(d_copy)

    return variable_histroy


def count_ngram(tokens, n):
    # variable_history = create_variable_history()
    # variable_to_type = {}
    decleared_cnt = 0

    # print(f"test:{variable_history}")

    for line in tokens:
        # 変数を型に置き換える処理
        replaced_line = []
        for i in range(len(line)):
            token = line[i]
            # 変数が宣言された場合，variable_to_typeを更新する
            # TODO:変数とxmlの対応を要確認
            # if token in set(['for', 'ex', 'let']):
            #     replaced_line.append(token)
            #     print(f'line:{line}')
            #     variable_to_type = variable_history[decleared_cnt]
            #     decleared_cnt += 1
            #     print(len(variable_history), decleared_cnt)
            
            # # 怪しい
            # elif token in variable_to_type:
            #     replaced_line.append(variable_to_type[token]+'(variable)')
            # else:
            #     replaced_line.append(token)

            if is_variable(line, i):
                replaced_line.append('___')
            else:
                replaced_line.append(token)

    
        # N-gramのパターンを保存，カウントする処理
        for index in range(len(line)-n+1):
            temp = replaced_line[index:index+n]
            key = ' '.join(temp)
            if not key in data:
                data[key] = 1
            else:
                data[key] += 1

mml_lar = open("/mnt/c/mizar/mml.lar", "r")

mizar_files = glob.glob(os.path.join(MML_DIR, '*.miz'))
# mizar_files = [os.path.join(MML_DIR, "graph_3a.miz")]
lexer = preprocess.Lexer()
lexer.load_symbol_dict(MML_VCT)
lexer.build_len2symbol()
count = 0
results = []

mml = []
file_names = []
for i in mml_lar.readlines():
    file_names.append(i.replace('\n', ''))
    mml.append(os.path.join(MML_DIR, i.replace('\n', '.miz')))

for filepath in mml:
    count += 1
    # 本来は1100で終了
    if count == 2:
        break
    lines = None
    with open('/mnt/c/mizar/mml/ring_1.miz', 'r') as f:
        try:
            lines = f.readlines()
            assert len(lines) > 0
        except:
            continue
    print(filepath)
    
    env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
    env_lines = lexer.remove_comment(env_lines)
    text_proper_lines = lexer.remove_comment(text_proper_lines)
    try:
        tokenized_lines, position_map = lexer.lex(text_proper_lines)
    except Exception:
        continue
    tokens = []
    for line in tokenized_lines:
        # i = re.sub('__\w+_', '', i)
        tokens.append(line.split())

    count_ngram(tokens, N)
    
result = sorted(data.items(), key=lambda x:x[1], reverse=True)

result_list = [i[0] for i in result if i[1]]
completions = {'completions': result_list}

with open('./output2_test.json', 'w') as f:
    json.dump(completions, f)

mml_lar.close()