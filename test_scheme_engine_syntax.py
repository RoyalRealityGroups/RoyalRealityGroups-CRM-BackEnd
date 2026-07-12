#!/usr/bin/env python3
"""Test scheme_engine.py for syntax and import errors"""
import sys
import py_compile

try:
    # Compile check
    py_compile.compile('/Users/bolluchaitanya/PythonProjects/Sales App/backend/Masters/scheme_engine.py', doraise=True)
    print("✅ scheme_engine.py: Syntax valid")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error in scheme_engine.py:")
    print(e)
    sys.exit(1)
