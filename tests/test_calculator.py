import sys
sys.path.append(".")
from app.tools import calculator

print("==== 正向用例测试 ====")
print("500*3 =", calculator("500*3"))
print("10+20 =", calculator("10+20"))
print("100/2 =", calculator("100/2"))
print("(5+3)*2 =", calculator("(5+3)*2"))

print("\n==== 异常输入用例 ====")
print("空字符串 =", calculator(""))
print("字母abc =", calculator("abc"))

print("\n==== 安全注入用例 ====")
print("恶意代码 =", calculator("__import__('os').system('dir')"))
