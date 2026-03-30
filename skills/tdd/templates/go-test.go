// $MODULE_NAME_test.go
// Test: $DESCRIPTION

package $PACKAGE

import "testing"

func Test$FUNCTION_NAME(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
		wantErr  bool
	}{
		{
			name:     "valid input",
			input:    "$INPUT",
			expected: "$EXPECTED",
			wantErr:  false,
		},
		{
			name:    "empty input",
			input:   "",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := $FUNCTION_NAME(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("$FUNCTION_NAME() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got != tt.expected {
				t.Errorf("$FUNCTION_NAME() = %v, want %v", got, tt.expected)
			}
		})
	}
}
