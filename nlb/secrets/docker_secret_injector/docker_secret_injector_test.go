package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestInjectSecretsFromPaths tests the core secret injection logic
func TestInjectSecretsFromPaths(t *testing.T) {
	// Create temporary directory for test secrets
	tmpDir := t.TempDir()

	tests := []struct {
		name         string
		setupEnv     map[string]string // Environment variables to set
		setupFiles   map[string]string // Files to create (path -> content)
		verbose      bool
		wantInjected []string          // Expected injected variable names
		wantEnvVars  map[string]string // Expected environment variable values
	}{
		{
			name: "basic secret injection",
			setupEnv: map[string]string{
				"TEST_SECRET_PATH": filepath.Join(tmpDir, "secret1"),
			},
			setupFiles: map[string]string{
				filepath.Join(tmpDir, "secret1"): "my-secret-value",
			},
			wantInjected: []string{"TEST_SECRET"},
			wantEnvVars: map[string]string{
				"TEST_SECRET": "my-secret-value",
			},
		},
		{
			name: "multiple secrets",
			setupEnv: map[string]string{
				"AWS_ACCESS_KEY_ID_PATH":     filepath.Join(tmpDir, "aws_key"),
				"AWS_SECRET_ACCESS_KEY_PATH": filepath.Join(tmpDir, "aws_secret"),
				"TS_AUTHKEY_PATH":            filepath.Join(tmpDir, "ts_key"),
			},
			setupFiles: map[string]string{
				filepath.Join(tmpDir, "aws_key"):    "AKIAIOSFODNN7EXAMPLE",
				filepath.Join(tmpDir, "aws_secret"): "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
				filepath.Join(tmpDir, "ts_key"):     "tskey-auth-123456",
			},
			wantInjected: []string{"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "TS_AUTHKEY"},
			wantEnvVars: map[string]string{
				"AWS_ACCESS_KEY_ID":     "AKIAIOSFODNN7EXAMPLE",
				"AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
				"TS_AUTHKEY":            "tskey-auth-123456",
			},
		},
		{
			name: "whitespace trimming",
			setupEnv: map[string]string{
				"TRIMMED_SECRET_PATH": filepath.Join(tmpDir, "trimmed"),
			},
			setupFiles: map[string]string{
				filepath.Join(tmpDir, "trimmed"): "  \n\t  secret-with-whitespace  \n\t  ",
			},
			wantInjected: []string{"TRIMMED_SECRET"},
			wantEnvVars: map[string]string{
				"TRIMMED_SECRET": "secret-with-whitespace",
			},
		},
		{
			name: "empty path skipped",
			setupEnv: map[string]string{
				"EMPTY_PATH_SECRET_PATH": "",
			},
			wantInjected: []string{},
			wantEnvVars:  map[string]string{},
		},
		{
			name: "missing file logs warning but continues",
			setupEnv: map[string]string{
				"MISSING_FILE_PATH": filepath.Join(tmpDir, "nonexistent"),
				"VALID_SECRET_PATH": filepath.Join(tmpDir, "valid"),
			},
			setupFiles: map[string]string{
				filepath.Join(tmpDir, "valid"): "valid-secret",
			},
			wantInjected: []string{"VALID_SECRET"},
			wantEnvVars: map[string]string{
				"VALID_SECRET": "valid-secret",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Clean up environment before test
			for key := range tt.setupEnv {
				defer os.Unsetenv(key)
				targetKey := strings.TrimSuffix(key, "_PATH")
				defer os.Unsetenv(targetKey)
			}

			// Create test files
			for path, content := range tt.setupFiles {
				if err := os.WriteFile(path, []byte(content), 0600); err != nil {
					t.Fatalf("Failed to create test file %s: %v", path, err)
				}
			}

			// Set up environment variables
			for key, value := range tt.setupEnv {
				if err := os.Setenv(key, value); err != nil {
					t.Fatalf("Failed to set env var %s: %v", key, err)
				}
			}

			// Run the injection
			injectSecretsFromPaths(tt.verbose)

			// Verify environment variable values - this is what actually matters
			for key, wantValue := range tt.wantEnvVars {
				gotValue := os.Getenv(key)
				if gotValue != wantValue {
					t.Errorf("Expected %s=%q, got %q", key, wantValue, gotValue)
				}
			}

			// Verify that expected variables were set
			for _, wantVar := range tt.wantInjected {
				if os.Getenv(wantVar) == "" {
					t.Errorf("Expected %s to be set, but it wasn't", wantVar)
				}
			}
		})
	}
}

// TestErrorCases tests error handling
func TestErrorCases(t *testing.T) {
	// Test file read errors are handled gracefully
	t.Run("file read error is logged", func(t *testing.T) {
		os.Setenv("UNREADABLE_SECRET_PATH", "/nonexistent/path/to/secret")
		defer os.Unsetenv("UNREADABLE_SECRET_PATH")
		defer os.Unsetenv("UNREADABLE_SECRET")

		// Should not panic, should log warning
		injectSecretsFromPaths(false)

		// Should not have injected the variable
		if os.Getenv("UNREADABLE_SECRET") != "" {
			t.Error("Should not have injected UNREADABLE_SECRET from nonexistent file")
		}
	})
}
