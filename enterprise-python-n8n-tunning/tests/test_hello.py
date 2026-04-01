def test_greet():
    from src.hello import greet

    assert greet("World") == "Hello, World!"


def test_add():
    from src.hello import add

    assert add(2, 3) == 5
