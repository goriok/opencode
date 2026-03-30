# tests/test_$MODULE_NAME.py
# Test: $DESCRIPTION

import pytest
from $MODULE_PATH import $FUNCTION_NAME


class TestFunctionName:
    def test_should_behave_correctly(self):
        result = $FUNCTION_NAME($INPUT)
        assert result == $EXPECTED

    def test_should_handle_empty_input(self):
        with pytest.raises(ValueError):
            $FUNCTION_NAME("")

    def test_should_handle_none(self):
        with pytest.raises(TypeError):
            $FUNCTION_NAME(None)
