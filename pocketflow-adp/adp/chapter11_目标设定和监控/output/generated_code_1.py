def gcd(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("参数必须是整数")
    
    a, b = abs(a), abs(b)
    
    if a == 0 and b == 0:
        raise ValueError("两个数不能同时为零")
    
    while b:
        a, b = b, a % b
    
    return a