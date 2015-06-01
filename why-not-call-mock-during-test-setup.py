#!/usr/bin/python

"""Here I argue why the mocked objects should not be called during a unit-
test setup stage.

People tend to do tests like this (see test_mock_call_incorrect below):

 def test_foobar():
    foo = mock.Mock()
    foo(42).method.return_value = 10
    foobar(foo)

    foo(42).method.assert_called_once()

While this works fine it introduces the following misthinking to the community:

 1. It makes people think that mock call foo(42) is different from any other.
    This is not true. Any call to a mock object returns exactly the same
    object:

    >>> m = mock.Mock()
    >>> m(10) == m(20)
    True

 2. It litters the mocked object call chain, making it harder to check for the
    call chain as a whole. Compare the following:

    >>> m = mock.Mock()
    >>> def foo(a):
    ...     return a(10).test(20).value
    >>> test = m(10).test = mock.Mock()
    >>> test(20).value = 10
    >>> assert foo(m) == 10
    >>> m.assert_has_calls([mock.call(10)])
    >>> test.assert_has_calls([mock.call(20)])
    >>> print(m.mock_calls)
    [call(10), call().test(20), call(10), call().test(20)]

    with:

    >>> m = mock.Mock(**{"return_value.test.return_value.value": 10})
    >>> def foo(a):
    ...     return a(10).test(20).value
    >>> assert foo(m) == 10
    >>> assert m.mock_calls == [mock.call(10), mock.call().test(20)]

 3. Making mock calls from the setup stage breaks the idea of unit-testing as
    such.  Mocks are to be called only from inside the method in test --
    because that is what are mocks for -- to simulate the object input object
    for a method and check for the method-in-test actions on the input object
    afterwards.

    So, calling a mock from the setup stage is breaking this pattern.
"""

import mock


def foobar(foo, bar):
    """foobar

    :param: foo -- a class
    :param: bar -- an instance with `method'
    """
    return foo(26).attr.method(bar.method())


def test_mock_call_correct():
    # Here I'm able to set the foo().attr.method.return_value without
    # extra calls and in a single line.
    foo = mock.Mock(**{"return_value.attr.method.return_value": 42})
    bar = mock.Mock()

    ret = foobar(foo, bar)
    assert ret == 42

    # Here I'm able to assert on the exact call list done *inside*
    # the method-in-test without necessity to deal with setup stage noise
    assert ([mock.call(26), mock.call(26).attr.method(bar.method.return_value)]
            == foo.mock_calls)


def test_mock_call_incorrect():
    foo = mock.Mock()
    bar = mock.Mock()
    # Here one is calling (incorrectly) a mock object to install the
    # return value of the method. Any of the following calls are still
    # providing the same result. So, the following are equivalently bad:
    # foo().attr.method.return_value = 42
    foo(26).attr.method.return_value = 42

    ret = foobar(foo, bar)
    assert ret == 42

    # The call during the setup is an extra call in the mock_calls.
    # This poisons mock_calls with a setup stage noise.
    # This breaks the idea of unit-testing because unit-test code
    # has to should be aware of side-effects. This complicates the
    # code.
    assert ([mock.call(26), mock.call(26),
            mock.call(26).attr.method(bar.method.return_value)] ==
            foo.mock_calls)

    # There is, however, a workaround. But assertion on the *exact*
    # calls happening in the method-in-test is not possible due to
    # setup stage call of foo(26).
    foo.assert_has_calls([
        mock.call(26), mock.call(26).attr.method(bar.method.return_value)])

    # Just to show that mocked objects calls are all the same
    # disregarding the args
    assert bar("foo") == bar("bar")


def regular_calls():
    class _AttrMethod(object):
        def __init__(self, v):
            self.v = v

        def method(self, o):
            return o + o + self.v

    class Foo(object):
        def __init__(self, v):
            self.attr = _AttrMethod(v)

    class Bar(object):
        def __init__(self, v):
            self.v = v

        def method(self):
            return self.v

    ret = foobar(Foo, Bar(8))
    assert ret == 42


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    regular_calls()
    test_mock_call_incorrect()
    test_mock_call_correct()
