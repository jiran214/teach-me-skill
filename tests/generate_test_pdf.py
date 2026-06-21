#!/usr/bin/env python3
"""生成模拟的PDF测试文档，模拟常见书籍格式"""

from fpdf import FPDF


def create_test_pdf(output_path: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 封面
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 60, "", ln=True)
    pdf.cell(0, 20, "Python Programming", ln=True, align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 15, "A Comprehensive Guide", ln=True, align="C")
    pdf.cell(0, 10, "", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "By John Smith", ln=True, align="C")
    pdf.cell(0, 10, "2024 Edition", ln=True, align="C")

    # 目录页
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Table of Contents", ln=True)
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    toc_items = [
        ("Chapter 1: Introduction to Python", 3),
        ("  1.1 What is Python?", 3),
        ("  1.2 Setting Up Your Environment", 4),
        ("  1.3 Your First Program", 5),
        ("Chapter 2: Data Types and Variables", 6),
        ("  2.1 Numbers", 6),
        ("  2.2 Strings", 7),
        ("  2.3 Lists", 8),
        ("Chapter 3: Control Flow", 9),
        ("  3.1 If Statements", 9),
        ("  3.2 Loops", 10),
        ("  3.3 Functions", 11),
    ]
    for item, page in toc_items:
        pdf.cell(0, 8, f"{item} {'.' * (50 - len(item))} {page}", ln=True)

    # 第1章
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Chapter 1: Introduction to Python", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "1.1 What is Python?", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "Python is a high-level, interpreted programming language known for its "
        "simplicity and readability. Created by Guido van Rossum and first released "
        "in 1991, Python has become one of the most popular programming languages "
        "in the world.\n\n"
        "Python emphasizes code readability with its notable use of significant "
        "whitespace. Its language constructs and object-oriented approach aim to "
        "help programmers write clear, logical code for small and large-scale "
        "projects."
    ))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "1.2 Setting Up Your Environment", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "To start programming in Python, you need to install Python on your "
        "computer. Visit python.org and download the latest version. After "
        "installation, you can verify it by running 'python --version' in your "
        "terminal.\n\n"
        "It is recommended to use a virtual environment for your projects. "
        "This keeps your project dependencies isolated from other projects."
    ))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "1.3 Your First Program", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "The traditional first program in any language is 'Hello, World!'. "
        "In Python, this is extremely simple:\n\n"
        "    print('Hello, World!')\n\n"
        "Save this in a file with .py extension and run it from the command "
        "line using 'python filename.py'. You should see the output displayed "
        "in your terminal."
    ))

    # 第2章
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Chapter 2: Data Types and Variables", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "2.1 Numbers", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "Python supports several types of numbers. The most common are integers "
        "(int) and floating-point numbers (float). Integers are whole numbers "
        "without a decimal point, while floats have a decimal point.\n\n"
        "Examples:\n"
        "    x = 5      # integer\n"
        "    y = 3.14   # float\n"
        "    z = 2 + 3j # complex number\n\n"
        "Python also supports arbitrary precision integers, which means you can "
        "work with numbers as large as your memory allows."
    ))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "2.2 Strings", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "Strings in Python are sequences of characters enclosed in quotes. "
        "You can use single quotes, double quotes, or triple quotes for "
        "multi-line strings.\n\n"
        "String operations are fundamental to Python programming. You can "
        "concatenate strings using the + operator, repeat them with *, and "
        "access individual characters using indexing."
    ))

    # 第3章
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Chapter 3: Control Flow", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "3.1 If Statements", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "If statements allow you to execute code conditionally. Python uses "
        "indentation to define code blocks, making the code visually clean "
        "and readable.\n\n"
        "The basic syntax is:\n"
        "    if condition:\n"
        "        # code to execute\n"
        "    elif another_condition:\n"
        "        # alternative code\n"
        "    else:\n"
        "        # default code"
    ))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "3.2 Loops", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "Python provides two types of loops: for loops and while loops. "
        "For loops iterate over a sequence, while loops continue until a "
        "condition becomes False.\n\n"
        "The for loop is particularly powerful in Python because it can "
        "iterate over any iterable object, including lists, strings, "
        "dictionaries, and custom objects."
    ))
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "3.3 Functions", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, (
        "Functions are reusable blocks of code that perform a specific task. "
        "They help organize code, reduce repetition, and make programs easier "
        "to understand and maintain.\n\n"
        "Define a function using the def keyword:\n"
        "    def greet(name):\n"
        "        return f'Hello, {name}!'\n\n"
        "Functions can have default parameters, return multiple values, and "
        "accept variable numbers of arguments."
    ))

    pdf.output(output_path)
    print(f"Generated test PDF: {output_path}")


if __name__ == "__main__":
    create_test_pdf("tests/sample_book.pdf")
