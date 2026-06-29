from utils.verification import generate_code


def test_generate_code_format():
    code = generate_code()
    
    assert isinstance(code, str)
    assert len(code) == 6
    assert code.isdigit()


def test_generate_code_randomness():
    code_a = generate_code()
    code_b = generate_code()
    
    assert code_a != code_b


def test_generate_code_multiple_times():
    codes = {generate_code() for _ in range(100)}
    
    for code in codes:
        assert len(code) == 6
        assert code.isdigit()
        
    assert len(codes) == 100