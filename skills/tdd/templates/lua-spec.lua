-- tests/$MODULE_NAME_spec.lua
-- Test: $DESCRIPTION

describe('$MODULE_NAME', function()
  local mod

  before_each(function()
    mod = require('$MODULE_PATH')
  end)

  it('should $BEHAVIOUR', function()
    local result = mod.$FUNCTION_NAME($INPUT)
    assert.are.equal($EXPECTED, result)
  end)

  it('should handle nil input', function()
    assert.has_error(function()
      mod.$FUNCTION_NAME(nil)
    end)
  end)
end)
