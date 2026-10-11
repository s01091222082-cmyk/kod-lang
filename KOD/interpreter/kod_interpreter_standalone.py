import sys
import random

variables = {}
functions = {}
classes = {}
var_types = {}  # 변수 이름 -> 처음 선언될 때의 타입 (재대입 시 타입 검사용)

MAX_LOOP = 1_000_000


class FunctionReturn(Exception):
    def __init__(self, value=None):
        self.value = value


class KODDict(list):
    """KOD 전용 딕셔너리. 순서를 가진 (키, 값) 쌍의 리스트."""
    def __str__(self):
        parts = []
        for key, value in self:
            key_text = repr(key) if isinstance(key, str) else str(key)
            value_text = repr(value) if isinstance(value, str) else str(value)
            parts.append(f"{key_text}: {value_text}")
        return "{" + ", ".join(parts) + "}"

    __repr__ = __str__


class KODClass:
    def __init__(self, name, params, methods):
        self.name = name
        self.params = params
        self.methods = methods  # {메서드이름: (매개변수목록, 본문줄들)}


class KODObject:
    def __init__(self, klass, values):
        self.klass = klass
        self.fields = dict(zip(klass.params, values))

    def __str__(self):
        parts = [f"{k}: {v!r}" if isinstance(v, str) else f"{k}: {v}" for k, v in self.fields.items()]
        return f"<{self.klass.name} " + ", ".join(parts) + ">"

    __repr__ = __str__


# ============================================================
# 토크나이저 + 파서 (계산식/값을 정확하게 해석하기 위한 부분)
# ============================================================

PUNCT = set("()[],:|+-*/.")


class Token:
    __slots__ = ("type", "value")

    def __init__(self, type_, value):
        self.type = type_
        self.value = value


def tokenize(text):
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        if ch == "'":
            j = i + 1
            buf = []
            while j < n and text[j] != "'":
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            if j >= n:
                raise SyntaxError("문자열이 따옴표로 안 닫혔어요.")
            tokens.append(Token("STRING", "".join(buf)))
            i = j + 1
            continue

        if ch.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            tokens.append(Token("NUMBER", int(text[i:j])))
            i = j
            continue

        if ch in PUNCT:
            tokens.append(Token(ch, ch))
            i += 1
            continue

        j = i
        while j < n and (not text[j].isspace()) and text[j] not in PUNCT and text[j] != "'":
            j += 1
        if j == i:
            raise SyntaxError(f"이해할 수 없는 글자예요: {ch!r}")
        tokens.append(Token("IDENT", text[i:j]))
        i = j

    tokens.append(Token("EOF", None))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def peek_next(self):
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, type_):
        tok = self.advance()
        if tok.type != type_:
            raise SyntaxError(f"'{type_}'가 필요한데 '{tok.value}'가 왔어요.")
        return tok

    def parse_expr(self):
        node = self.parse_term()
        while self.peek().type in ("+", "-"):
            op = self.advance().type
            right = self.parse_term()
            node = ("binop", op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().type in ("*", "/"):
            op = self.advance().type
            right = self.parse_factor()
            node = ("binop", op, node, right)
        return node

    def parse_factor(self):
        if self.peek().type == "-":
            self.advance()
            return ("neg", self.parse_factor())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.type == "NUMBER":
            self.advance()
            return ("num", tok.value)

        if tok.type == "STRING":
            self.advance()
            return ("str", tok.value)

        if tok.type == "(":
            self.advance()
            node = self.parse_expr()
            self.expect(")")
            return node

        if tok.type == "[":
            self.advance()
            items = []
            if self.peek().type != "]":
                items.append(self.parse_expr())
                while self.peek().type == ",":
                    self.advance()
                    items.append(self.parse_expr())
            self.expect("]")
            return ("list", items)

        if tok.type == "|":
            self.advance()
            self.expect("|")
            entries = []
            if not (self.peek().type == "|"):
                entries.append(self.parse_dict_entry())
                while self.peek().type == ",":
                    self.advance()
                    entries.append(self.parse_dict_entry())
            self.expect("|")
            self.expect("|")
            return ("dict", entries)

        if tok.type == "IDENT":
            return self.parse_ident_chain()

        raise SyntaxError(f"이해할 수 없는 값이에요: {tok.value!r}")

    def parse_dict_entry(self):
        key_tok = self.advance()
        if key_tok.type == "STRING":
            key_node = ("str", key_tok.value)
        elif key_tok.type == "IDENT":
            key_node = ("bareword", key_tok.value)
        else:
            raise SyntaxError("딕셔너리 키는 글자나 이름이어야 해요.")
        self.expect(":")
        value_node = self.parse_expr()
        return (key_node, value_node)

    def parse_args(self):
        args = []
        if self.peek().type != ")":
            args.append(self.parse_expr())
            while self.peek().type == ",":
                self.advance()
                args.append(self.parse_expr())
        self.expect(")")
        return args

    def parse_ident_chain(self):
        first = self.advance().value
        parts = [first]
        while self.peek().type == "." and self.peek_next().type == "IDENT":
            self.advance()
            parts.append(self.advance().value)

        if self.peek().type == "(":
            self.advance()
            args = self.parse_args()
            return ("call", parts, args)

        return ("name", parts)


def get_value(text):
    text = text.strip()
    if text == "":
        raise SyntaxError("값이 비어 있어요.")
    tokens = tokenize(text)
    parser = Parser(tokens)
    node = parser.parse_expr()
    if parser.peek().type != "EOF":
        raise SyntaxError(f"'{parser.peek().value}' 근처 문법이 이상해요.")
    return eval_node(node)


def eval_dict_key(key_node):
    if key_node[0] == "str":
        return key_node[1]
    name = key_node[1]
    if name in variables:
        return variables[name]
    return name  # 따옴표 없는 딕셔너리 키는 그대로 글자로 취급 (기존 관례 유지)


def resolve_name(parts):
    first = parts[0]

    if first == "참":
        base = True
    elif first == "거짓":
        base = False
    elif first in variables:
        base = variables[first]
    else:
        raise NameError(f"'{first}'라는 변수가 없어요. (글자라면 따옴표를 빼먹지 않았는지 확인해보세요)")

    for seg in parts[1:]:
        if not isinstance(base, KODObject):
            raise AttributeError(f"'{seg}'에 접근할 수 없어요.")
        if seg not in base.fields:
            raise AttributeError(f"'{base.klass.name}'에는 '{seg}' 속성이 없어요.")
        base = base.fields[seg]

    return base


def resolve_call(parts, arg_nodes):
    if parts == ["주사위", "숫자"]:
        args = [eval_node(a) for a in arg_nodes]
        if len(args) != 2 or not all(isinstance(a, int) and not isinstance(a, bool) for a in args):
            raise TypeError("주사위.숫자는 (시작숫자, 끝낼숫자) 형식이에요.")
        return random.randint(args[0], args[1])

    if parts == ["주사위", "고르기"]:
        if len(arg_nodes) == 1:
            choices = eval_node(arg_nodes[0])
            if isinstance(choices, str):
                return choices
            if not isinstance(choices, list):
                raise TypeError("주사위.고르기는 리스트나 글자를 고를 수 있어요.")
            choices = list(choices)
        else:
            choices = [eval_node(a) for a in arg_nodes]
        if not choices:
            raise ValueError("주사위.고르기에 고를 값이 없어요.")
        return random.choice(choices)

    if len(parts) == 1:
        name = parts[0]

        if name == "크기":
            if len(arg_nodes) != 1:
                raise ValueError("크기()는 값 하나만 받아요.")
            target = eval_node(arg_nodes[0])
            try:
                return len(target)
            except TypeError:
                raise TypeError("크기()는 글자, 리스트, 딕셔너리 등에 사용할 수 있어요.")

        if name == "합계":
            if len(arg_nodes) != 1:
                raise ValueError("합계()는 리스트 하나만 받아요.")
            target = eval_node(arg_nodes[0])
            if not isinstance(target, list) or isinstance(target, KODDict):
                raise TypeError("합계()는 리스트에만 사용할 수 있어요.")
            if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in target):
                raise TypeError("합계()는 숫자로만 이루어진 리스트여야 해요.")
            return sum(target)

        if name == "최대":
            if len(arg_nodes) != 1:
                raise ValueError("최대()는 리스트 하나만 받아요.")
            target = eval_node(arg_nodes[0])
            if not isinstance(target, list) or isinstance(target, KODDict):
                raise TypeError("최대()는 리스트에만 사용할 수 있어요.")
            if not target:
                raise ValueError("빈 리스트에는 최대()를 쓸 수 없어요.")
            return max(target)

        if name == "최소":
            if len(arg_nodes) != 1:
                raise ValueError("최소()는 리스트 하나만 받아요.")
            target = eval_node(arg_nodes[0])
            if not isinstance(target, list) or isinstance(target, KODDict):
                raise TypeError("최소()는 리스트에만 사용할 수 있어요.")
            if not target:
                raise ValueError("빈 리스트에는 최소()를 쓸 수 없어요.")
            return min(target)

        if name == "뒤집기":
            if len(arg_nodes) != 1:
                raise ValueError("뒤집기()는 리스트나 글자 하나만 받아요.")
            target = eval_node(arg_nodes[0])
            if isinstance(target, str):
                return target[::-1]
            if isinstance(target, list) and not isinstance(target, KODDict):
                return list(reversed(target))
            raise TypeError("뒤집기()는 리스트나 글자에만 사용할 수 있어요.")

        if name in classes:
            klass = classes[name]
            args = [eval_node(a) for a in arg_nodes]
            if len(args) != len(klass.params):
                raise ValueError(f"'{name}'은 {len(klass.params)}개의 값이 필요해요.")
            return KODObject(klass, args)

        if name in functions:
            args = [eval_node(a) for a in arg_nodes]
            return call_user_function(name, args)

        raise NameError(f"'{name}'이라는 함수가 없어요.")

    obj_parts, method_name = parts[:-1], parts[-1]
    obj = resolve_name(obj_parts)
    if not isinstance(obj, KODObject):
        raise AttributeError(f"'{method_name}'을 호출할 수 없어요.")
    if method_name not in obj.klass.methods:
        raise AttributeError(f"'{obj.klass.name}'에는 '{method_name}' 기능이 없어요.")
    args = [eval_node(a) for a in arg_nodes]
    return call_object_method(obj, method_name, args)


def eval_node(node):
    kind = node[0]

    if kind == "num":
        return node[1]
    if kind == "str":
        return node[1]

    if kind == "neg":
        val = eval_node(node[1])
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise TypeError("음수 부호(-)는 숫자에만 쓸 수 있어요.")
        return -val

    if kind == "binop":
        op = node[1]
        left = eval_node(node[2])
        right = eval_node(node[3])

        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right

    if kind == "list":
        return [eval_node(x) for x in node[1]]

    if kind == "dict":
        result = KODDict()
        for key_node, value_node in node[1]:
            result.append((eval_dict_key(key_node), eval_node(value_node)))
        return result

    if kind == "bareword":
        return eval_dict_key(node)

    if kind == "name":
        return resolve_name(node[1])

    if kind == "call":
        return resolve_call(node[1], node[2])

    raise SyntaxError("알 수 없는 표현식이에요.")


# ============================================================
# 조건문 (만약/계속해 등에서 쓰는 한국어 비교 연산자)
# ============================================================

def check_simple_condition(condition):
    condition = condition.strip()
    operators = ["==", "않다", "이상", "이하", "크다", "작다"]

    for operator in operators:
        if operator in condition:
            left, right = condition.split(operator, 1)
            left = get_value(left)
            right = get_value(right)

            if operator == "==":
                return left == right
            elif operator == "않다":
                return left != right
            elif operator == "크다":
                return left > right
            elif operator == "작다":
                return left < right
            elif operator == "이상":
                return left >= right
            elif operator == "이하":
                return left <= right

    result = get_value(condition)
    if result is True:
        return True
    if result is False:
        return False
    return False


def check_condition(condition):
    if " 그리고 " in condition:
        return all(check_condition(part) for part in condition.split(" 그리고 "))
    if " 또는 " in condition:
        return any(check_condition(part) for part in condition.split(" 또는 "))
    return check_simple_condition(condition)


def print_kod(text):
    value = get_value(text)
    if value is True:
        print("참")
    elif value is False:
        print("거짓")
    else:
        print(str(value).replace("\\줄", "\n"))


# ============================================================
# 리스트/딕셔너리 조작 도우미 (기존 문법 인자 파싱은 split_args 유지)
# ============================================================

def split_args(text):
    """쉼표를 기준으로 인자를 나누되 문자열/리스트/딕셔너리/괄호 안의 쉼표는 무시한다."""
    args = []
    current = []
    depth_square = 0
    depth_paren = 0
    depth_pipe = 0
    in_string = False
    escaped = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and in_string:
            current.append(char)
            escaped = True
            continue
        if char == "'":
            in_string = not in_string
            current.append(char)
            continue
        if not in_string:
            if char == "[":
                depth_square += 1
            elif char == "]":
                depth_square -= 1
            elif char == "(":
                depth_paren += 1
            elif char == ")":
                depth_paren -= 1
            elif char == "|":
                depth_pipe = 1 - depth_pipe
            elif char == "," and depth_square == 0 and depth_paren == 0 and depth_pipe == 0:
                args.append("".join(current).strip())
                current = []
                continue
        current.append(char)

    if current or text.strip():
        args.append("".join(current).strip())

    return args


DECLARE_KEYWORDS = ["숫자", "글자", "불", "리스트", "딕셔너리"]


def check_declared_type(type_name, value):
    """엄격한 타입 검사 - 안 맞으면 그냥 TypeError를 낸다 (예전처럼 강제 변환 안 함)."""
    if type_name == "숫자":
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"'숫자'라고 선언했는데 숫자가 아닌 값이에요: {value!r}")
    elif type_name == "글자":
        if not isinstance(value, str):
            raise TypeError(f"'글자'라고 선언했는데 글자가 아닌 값이에요: {value!r}")
    elif type_name == "불":
        if not isinstance(value, bool):
            raise TypeError(f"'불'이라고 선언했는데 참/거짓이 아닌 값이에요: {value!r}")
    elif type_name == "리스트":
        if not isinstance(value, list) or isinstance(value, KODDict):
            raise TypeError(f"'리스트'라고 선언했는데 리스트가 아닌 값이에요: {value!r}")
    elif type_name == "딕셔너리":
        if not isinstance(value, KODDict):
            raise TypeError(f"'딕셔너리'라고 선언했는데 딕셔너리가 아닌 값이에요: {value!r}")
    elif type_name in classes:
        if not isinstance(value, KODObject) or value.klass.name != type_name:
            raise TypeError(f"'{type_name}' 타입인데 그 클래스의 객체가 아니에요: {value!r}")
    else:
        raise ValueError(f"알 수 없는 타입이에요: {type_name}")
    return value


def list_add(name, args):
    if name not in variables or not isinstance(variables[name], list) or isinstance(variables[name], KODDict):
        raise TypeError(f"'{name}'은 리스트가 아니에요.")
    if len(args) != 3:
        raise ValueError("리스트.추가하기는 [칸번호, 타입, 값] 형식이에요.")

    index = get_value(args[0])
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("칸번호는 숫자여야 해요.")
    if index < 0:
        raise IndexError("칸번호는 0 이상이어야 해요.")

    type_name = args[1].strip()
    value = check_declared_type(type_name, get_value(args[2]))

    while len(variables[name]) < index:
        variables[name].append("null")

    if index == len(variables[name]):
        variables[name].append(value)
    else:
        variables[name][index] = value


def list_remove(name, args):
    if name not in variables or not isinstance(variables[name], list) or isinstance(variables[name], KODDict):
        raise TypeError(f"'{name}'은 리스트가 아니에요.")
    if len(args) != 2:
        raise ValueError("리스트.빼기는 [칸번호, 타입] 형식이에요.")

    index = get_value(args[0])
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("칸번호는 숫자여야 해요.")
    if index < 0 or index >= len(variables[name]):
        raise IndexError("존재하지 않는 리스트 칸번호예요.")

    variables[name].pop(index)


def dict_add(name, args):
    if name not in variables or not isinstance(variables[name], KODDict):
        raise TypeError(f"'{name}'은 딕셔너리가 아니에요.")
    if len(args) != 3:
        raise ValueError("딕셔너리.추가는 [인덱스, 타입, 키: 값] 형식이에요.")

    index = get_value(args[0])
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("인덱스는 숫자여야 해요.")
    if index < 0:
        raise IndexError("인덱스는 0 이상이어야 해요.")

    content = args[2].strip()
    if ":" not in content:
        raise ValueError("딕셔너리 내용은 키: 값 형식이어야 해요.")
    key_text, value_text = content.split(":", 1)
    key = eval_dict_key(("bareword", key_text.strip())) if not key_text.strip().startswith("'") else get_value(key_text.strip())
    type_name = args[1].strip()
    value = check_declared_type(type_name, get_value(value_text.strip()))

    while len(variables[name]) < index:
        variables[name].append(("null", "null"))

    entry = (key, value)
    if index == len(variables[name]):
        variables[name].append(entry)
    else:
        variables[name][index] = entry


def dict_remove(name, args):
    if name not in variables or not isinstance(variables[name], KODDict):
        raise TypeError(f"'{name}'은 딕셔너리가 아니에요.")
    if len(args) != 1:
        raise ValueError("딕셔너리.빼기는 [키] 형식이에요.")

    key = eval_dict_key(("bareword", args[0])) if not args[0].strip().startswith("'") else get_value(args[0])
    for idx, (entry_key, _) in enumerate(variables[name]):
        if entry_key == key:
            variables[name].pop(idx)
            return
    raise KeyError(f"딕셔너리에 '{key}' 키가 없어요.")


# ============================================================
# 함수 / 클래스 호출
# ============================================================

def call_user_function(name, arg_values):
    params, body = functions[name]
    if len(arg_values) != len(params):
        raise ValueError(f"함수 '{name}'에는 {len(params)}개의 값이 필요해요.")

    old_values = {p: variables.get(p) for p in params}
    old_exists = {p: p in variables for p in params}
    try:
        for p, v in zip(params, arg_values):
            variables[p] = v
        try:
            execute_range(body, 0, len(body))
        except FunctionReturn as r:
            return r.value
        return None
    finally:
        for p in params:
            if old_exists[p]:
                variables[p] = old_values[p]
            else:
                variables.pop(p, None)


def call_object_method(obj, method_name, arg_values):
    params, body = obj.klass.methods[method_name]
    if len(arg_values) != len(params):
        raise ValueError(f"메서드 '{method_name}'에는 {len(params)}개의 값이 필요해요.")

    bind_names = list(obj.fields.keys()) + params
    old_values = {n: variables.get(n) for n in bind_names}
    old_exists = {n: n in variables for n in bind_names}

    try:
        for k, v in obj.fields.items():
            variables[k] = v
        for p, v in zip(params, arg_values):
            variables[p] = v

        result = None
        try:
            execute_range(body, 0, len(body))
        except FunctionReturn as r:
            result = r.value

        for k in obj.fields:
            if k in variables:
                obj.fields[k] = variables[k]

        return result
    finally:
        for n in bind_names:
            if old_exists[n]:
                variables[n] = old_values[n]
            else:
                variables.pop(n, None)


# ============================================================
# 에러 메시지
# ============================================================

ERROR_MESSAGES = {
    "TypeError": ("이상한글자오류", "타입을 다시 확인해주십시오. 타입끼리 싸우고 있읍니다."),
    "ValueError": ("값이왜이래오류", "값을 다시 확인해주십시오. 값이 마음에 들지 않는다고 합니다."),
    "IndexError": ("거기자리는없는데요오류", "존재하는 인덱스를 사용해주십시오. 그 자리는 비어있읍니다."),
    "KeyError": ("키를잃어버렸어요오류", "존재하는 키를 사용해주십시오. 키가 어디 갔는지 모르겠읍니다."),
    "NameError": ("누가그런변수만들래오류", "존재하는 변수를 사용해주십시오. 없는 변수는 찾을 수 없읍니다. 글자라면 따옴표를 확인해주십시오."),
    "ZeroDivisionError": ("0은나눠먹는게아닙니다오류", "0으로 나누지 마십시오. 수학 선생님이 화냅니다."),
    "SyntaxError": ("이게뭔말이야오류", "KOD 문법에 맞게 작성해주십시오. 저도 무슨 말인지 모르겠읍니다."),
    "AttributeError": ("그런기능없는데요오류", "존재하는 기능/속성을 사용해주십시오. 제가 찾아봤는데 없읍니다."),
    "RecursionError": ("함수가자기자신을너무좋아해요오류", "함수 호출을 적당히 멈춰주십시오. 계속 자기 자신을 부르고 있읍니다."),
}


def format_kod_error(line_number, line, error):
    error_type = type(error).__name__
    error_name, wanted = ERROR_MESSAGES.get(
        error_type,
        ("정체불명오류", "문제의 원인을 확인해주십시오. 저도 처음 보는 문제입니다."),
    )
    message = str(error)
    detail = f" ({message})" if message else ""
    return f"Line : {line_number}\n에러 : {error_name}\n원하는 것 : {wanted}{detail}"


# ============================================================
# 문장(statement) 실행
# ============================================================

def execute_statement(line):
    line = line.strip()
    if not line:
        return

    if line == "돌아가!":
        raise FunctionReturn()
    if line.startswith("돌아가!(") and line.endswith(")"):
        raise FunctionReturn(get_value(line[5:-1]))

    if line.startswith("말해(") and line.endswith(")"):
        print_kod(line[3:-1])
        return

    if ".추가(" in line and line.endswith(")"):
        name, rest = line.split(".추가(", 1)
        name = name.strip()
        args = split_args(rest[:-1])
        if name in variables and isinstance(variables[name], KODDict):
            dict_add(name, args)
            return
        if name in variables and isinstance(variables[name], list):
            list_add(name, args)
            return

    if ".삭제(" in line and line.endswith(")"):
        name, rest = line.split(".삭제(", 1)
        name = name.strip()
        args = split_args(rest[:-1])
        if name in variables and isinstance(variables[name], KODDict):
            if len(args) != 1:
                raise ValueError("딕셔너리.삭제는 [키] 형식이에요.")
            dict_remove(name, args)
            return
        if name in variables and isinstance(variables[name], list):
            list_remove(name, args)
            return

    if ".추가하기[" in line and line.endswith("]"):
        name, rest = line.split(".추가하기[", 1)
        list_add(name.strip(), split_args(rest[:-1]))
        return

    if ".빼기[" in line and line.endswith("]"):
        name, rest = line.split(".빼기[", 1)
        name = name.strip()
        args = split_args(rest[:-1])
        # KODDict는 list를 상속하므로 반드시 KODDict를 먼저 검사해야 함
        if name in variables and isinstance(variables[name], KODDict):
            dict_remove(name, args)
            return
        if name in variables and isinstance(variables[name], list):
            list_remove(name, args)
            return
        raise NameError(f"'{name}'을 찾을 수 없어요.")

    if ".추가[" in line and line.endswith("]"):
        name, rest = line.split(".추가[", 1)
        dict_add(name.strip(), split_args(rest[:-1]))
        return

    # 함수/클래스 호출을 문장으로 사용 (반환값 무시)
    if line.endswith(")") and "(" in line:
        try:
            tokens = tokenize(line)
            node = Parser(tokens).parse_expr()
        except SyntaxError:
            node = None
        if node is not None and node[0] == "call":
            eval_node(node)
            return

    # 객체.필드 = 값
    if "=" in line and "==" not in line:
        left, right = line.split("=", 1)
        left = left.strip()

        if "." in left and "(" not in left and "[" not in left:
            obj_name, field_name = left.rsplit(".", 1)
            obj_name = obj_name.strip()
            field_name = field_name.strip()
            if obj_name in variables and isinstance(variables[obj_name], KODObject):
                variables[obj_name].fields[field_name] = get_value(right)
                return
            raise NameError(f"'{obj_name}'이라는 객체가 없어요.")

        # 타입 접두사가 있는 변수 선언/대입 (처음 선언이든, 타입을 다시 명시한 대입이든)
        matched_prefix = False
        for kw in DECLARE_KEYWORDS + list(classes.keys()):
            prefix = kw + " "
            if line.startswith(prefix):
                rest = line[len(prefix):]
                name, value_text = rest.split("=", 1)
                name = name.strip()
                if not name:
                    raise SyntaxError("변수 이름이 비어 있어요.")
                value = check_declared_type(kw, get_value(value_text))
                variables[name] = value
                var_types[name] = kw
                matched_prefix = True
                return

        if not matched_prefix:
            # 타입 접두사 없는 대입 - 이미 선언된 변수의 재대입만 허용
            if left not in variables:
                raise SyntaxError(
                    f"'{left}'에 값을 넣으려면 앞에 타입(숫자/글자/불/리스트/딕셔너리 또는 클래스 이름)을 꼭 붙여야 해요. "
                    f"(처음 선언할 때만 필요해요)"
                )
            new_value = get_value(right)
            declared_type = var_types.get(left)
            if declared_type is not None:
                new_value = check_declared_type(declared_type, new_value)
            variables[left] = new_value
            return

    raise SyntaxError("알 수 없는 문장이에요.")


# ============================================================
# 블록(여러 줄) 실행
# ============================================================

def indentation(line):
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def find_block_end(lines, header_index):
    if header_index + 1 >= len(lines):
        return header_index + 1

    parent_indent = indentation(lines[header_index])
    if not lines[header_index + 1].strip() or indentation(lines[header_index + 1]) <= parent_indent:
        return header_index + 1

    j = header_index + 1
    while j < len(lines):
        clean = lines[j].strip()
        if clean and indentation(lines[j]) <= parent_indent:
            break
        j += 1
    return j


def parse_header_params(header_after_name):
    """'(a, b)' 형태에서 매개변수 이름 목록을 뽑는다."""
    inside = header_after_name[:-1]  # 마지막 ')' 제거
    if not inside.strip():
        return []
    params = [x.strip() for x in split_args(inside)]
    if any(not p for p in params):
        raise ValueError("매개변수 이름이 비어 있어요.")
    return params


def execute_range(lines, start, end):
    i = start

    while i < end:
        line = lines[i].rstrip("\n\r")
        clean = line.strip()

        if not clean:
            i += 1
            continue

        try:
            # 함수 정의
            if clean.startswith("함수 ") and "(" in clean and clean.endswith(")"):
                header = clean[3:].strip()
                name, inside = header.split("(", 1)
                name = name.strip()
                params = parse_header_params(inside)
                block_end = find_block_end(lines, i)
                functions[name] = (params, lines[i + 1:block_end])
                i = block_end
                continue

            # 클래스 정의
            if clean.startswith("클래스 ") and "(" in clean and clean.endswith(")"):
                header = clean[4:].strip()
                name, inside = header.split("(", 1)
                name = name.strip()
                field_params = parse_header_params(inside)

                class_block_end = find_block_end(lines, i)
                methods = {}
                j = i + 1
                while j < class_block_end:
                    m_clean = lines[j].strip()
                    if not m_clean:
                        j += 1
                        continue
                    if m_clean.startswith("함수 ") and "(" in m_clean and m_clean.endswith(")"):
                        m_header = m_clean[3:].strip()
                        m_name, m_inside = m_header.split("(", 1)
                        m_name = m_name.strip()
                        m_params = parse_header_params(m_inside)
                        m_block_end = find_block_end(lines, j)
                        methods[m_name] = (m_params, lines[j + 1:m_block_end])
                        j = m_block_end
                        continue
                    raise SyntaxError("클래스 안에는 함수(메서드)만 넣을 수 있어요.")

                classes[name] = KODClass(name, field_params, methods)
                i = class_block_end
                continue

            # 만약 / 또아니면 / 아니면 체인
            if clean.startswith("만약("):
                chain_end = i
                branches = []
                first_indent = indentation(lines[i])

                while chain_end < end:
                    branch_clean = lines[chain_end].strip()
                    if chain_end != i and indentation(lines[chain_end]) != first_indent:
                        break

                    if branch_clean.startswith("만약("):
                        condition = branch_clean[3:-1]
                    elif branch_clean.startswith("또아니면("):
                        condition = branch_clean[5:-1]
                    elif branch_clean == "아니면":
                        condition = None
                    else:
                        break

                    block_end = find_block_end(lines, chain_end)
                    branches.append((condition, chain_end + 1, block_end))
                    chain_end = block_end

                    if chain_end >= end:
                        break
                    next_clean = lines[chain_end].strip()
                    if not (next_clean.startswith("또아니면(") or next_clean == "아니면"):
                        break

                for condition, body_start, body_end in branches:
                    if condition is None or check_condition(condition):
                        execute_range(lines, body_start, body_end)
                        break

                i = chain_end
                continue

            if clean.startswith("또아니면(") or clean == "아니면":
                i = find_block_end(lines, i)
                continue

            # 계속해() - while
            if clean.startswith("계속해(") and clean.endswith(")"):
                condition = clean[4:-1]
                block_end = find_block_end(lines, i)
                loop_count = 0

                while check_condition(condition):
                    execute_range(lines, i + 1, block_end)
                    loop_count += 1
                    if loop_count >= MAX_LOOP:
                        print(f"[{i + 1}번째 줄] 계속해()가 {MAX_LOOP}번 넘게 반복돼서 강제로 멈췄어요.")
                        break

                i = block_end
                continue

            # 한번씩() - for
            if clean.startswith("한번씩(") and clean.endswith(")"):
                inside = clean[4:-1]
                args = split_args(inside)
                if len(args) != 2:
                    raise ValueError("한번씩은 (변수, 횟수) 형식이에요.")

                var_name = args[0].strip()
                count = get_value(args[1])
                if not isinstance(count, int) or isinstance(count, bool):
                    raise TypeError("한번씩의 횟수는 숫자여야 해요.")

                block_end = find_block_end(lines, i)
                for n in range(1, count + 1):
                    variables[var_name] = n
                    execute_range(lines, i + 1, block_end)

                i = block_end
                continue

            execute_statement(clean)

        except FunctionReturn:
            raise
        except Exception as e:
            print(format_kod_error(i + 1, clean, e))

        i += 1


def run_kod(filename):
    global variables, functions, classes, var_types
    variables = {}
    functions = {}
    classes = {}
    var_types = {}

    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    execute_range(lines, 0, len(lines))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("how to use: python interpreter.py <filename.kod>")
    else:
        run_kod(sys.argv[1])
