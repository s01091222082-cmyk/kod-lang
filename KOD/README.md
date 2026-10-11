# KOD — Korean Programming Language

**KOD** is a custom programming language that uses Korean keywords and runs through an interpreter written in Python.

I started developing KOD as a personal project and also created a VS Code extension to make writing KOD code easier.

My goal is to build a programming language that allows users to write code using Korean keywords instead of relying entirely on English keywords.

KOD is still a work in progress!

## ✨ Features

- Korean keywords for programming
- Python-based interpreter
- VS Code extension
- Variables and basic data types
- Arithmetic and comparison operators
- Conditional statements
- Loops
- Lists and dictionaries
- Functions and return values
- Random number generation and random selection
- User input
- Korean error messages
- A working rock-paper-scissors game written in KOD

## 🚀 Example

Here is a simple example of KOD:

```kod
숫자 점수 = 15

만약(점수 크다 10)
    말해('승리!')
아니면
    말해('다시 도전!')
```

Output:

```text
승리!
```

## 📖 Syntax Guide

### 1. Output

Use `말해()` to display a value.

```kod
말해('Hello, KOD!')
말해(123)
```

### 2. Variables and Data Types

KOD supports typed variable declarations.

| Keyword | Meaning |
|---|---|
| `숫자` | Number |
| `글자` | String |
| `불` | Boolean |
| `리스트` | List |
| `딕셔너리` | Dictionary |

Examples:

```kod
숫자 점수 = 100
글자 이름 = 'KOD'
불 게임중 = 참
```

Boolean values:

```kod
불 성공 = 참
불 실패 = 거짓
```

Variables can also be reassigned:

```kod
숫자 점수 = 10
점수 = 점수 + 5

말해(점수)
```

Output:

```text
15
```

### 3. Arithmetic Operators

KOD supports basic arithmetic.

| Operator | Meaning |
|---|---|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `()` | Grouping expressions |

Example:

```kod
숫자 결과 = (10 + 5) * 2
말해(결과)
```

### 4. Comparison Operators

KOD uses Korean comparison keywords as well as `==`.

| Operator | Meaning |
|---|---|
| `==` | Equal to |
| `않다` | Not equal to |
| `크다` | Greater than |
| `작다` | Less than |
| `이상` | Greater than or equal to |
| `이하` | Less than or equal to |

Examples:

```kod
만약(10 크다 5)
    말해('10 is greater than 5')
```

```kod
만약(10 이상 10)
    말해('The condition is true')
```

### 5. Logical Operators

| Operator | Meaning |
|---|---|
| `그리고` | AND |
| `또는` | OR |

Example:

```kod
숫자 점수 = 80

만약(점수 이상 60 그리고 점수 이하 100)
    말해('Passed!')
```

### 6. Conditional Statements

KOD supports `만약`, `또아니면`, and `아니면`.

```kod
숫자 점수 = 85

만약(점수 이상 90)
    말해('Excellent!')
또아니면(점수 이상 60)
    말해('Passed!')
아니면
    말해('Failed!')
```

- `만약` — If
- `또아니면` — Else if
- `아니면` — Else

Indentation is used to organize code blocks.

### 7. While Loops

Use `계속해()` to repeat a block while a condition is true.

```kod
숫자 i = 1

계속해(i 이하 5)
    말해(i)
    i = i + 1
```

### 8. For Loops

Use `한번씩()` to iterate over a range.

```kod
한번씩(i, 크기(5))
    말해(i)
```

KOD's loop indexing and range behavior may differ from Python's, so check the interpreter's current implementation when using ranges.

### 9. Lists

Lists use square brackets.

```kod
리스트 숫자들 = [1, 2, 3, 4, 5]

말해(숫자들)
말해(크기(숫자들))
```

KOD also provides list operations such as adding and removing elements through its collection methods.

### 10. Dictionaries

Dictionaries use `||` as delimiters.

```kod
딕셔너리 정보 = ||'이름': 'KOD', '버전': 13||

말해(정보)
```

Dictionaries store key-value pairs. The exact supported operations depend on the current interpreter version.

### 11. Functions

Functions are declared using `함수`.

```kod
함수 인사(이름)
    말해('Hello!')
```

A function can return a value using `돌아가!`.

```kod
함수 더하기(a, b)
    돌아가! a + b
```

Function syntax and supported argument behavior may depend on the interpreter version.

### 12. User Input

Use `입력()` to receive input from the user.

```kod
글자 이름 = 입력('What is your name? ')
말해(이름)
```

### 13. Random Operations

KOD provides random utilities through `주사위`.

Generate a random number:

```kod
숫자 결과 = 주사위.숫자(1, 10)
말해(결과)
```

Choose a random item:

```kod
글자 선택 = 주사위.고르기(['가위', '바위', '보'])
말해(선택)
```

### 14. New Lines

KOD supports `\줄` for a newline sequence in supported strings.

## 🎮 Example Project: Rock-Paper-Scissors

One of my first working projects written in KOD is a rock-paper-scissors game.

The game includes:

- User input
- Random computer choices
- Win, loss, and draw detection
- Score tracking
- A command to exit the game

This project helped me test KOD's input handling, conditions, random selection, and variables.

## 🛠️ Built With

- **Python** — Interpreter implementation
- **Visual Studio Code** — Development environment
- **VS Code Extension API** — KOD editing support

## 📌 Project Status

KOD is an experimental programming language under active development.

Its syntax, features, and implementation may change as development continues.

## 💬 Feedback

I'd love to hear your thoughts!

- What feature should I add next?
- What could be improved about the syntax?
- What kinds of programs would you like to see written in KOD?

Thanks for checking out my project!

---

**Made with Python and a lot of experimentation.**
