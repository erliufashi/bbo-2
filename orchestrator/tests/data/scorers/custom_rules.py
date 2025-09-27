"""测试使用的自定义评分脚本。"""

def score(*, expected, actual, context):
    """若实际值大于等于预期则通过。"""
    passed = actual >= expected
    return {"score": 1.0 if passed else 0.0, "pass_": passed, "reasoning": "阈值比较"}
