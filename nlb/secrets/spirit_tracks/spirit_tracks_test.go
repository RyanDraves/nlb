package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// TestLoadConfig tests the configuration file loading and parsing
func TestLoadConfig(t *testing.T) {
	tmpDir := t.TempDir()

	tests := []struct {
		name        string
		configJSON  string
		wantErr     bool
		errContains string
		validate    func(*testing.T, *Config)
	}{
		{
			name: "valid config without uid",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/app",
						"values": ["app/secret1", "app/secret2"]
					}
				]
			}`,
			wantErr: false,
			validate: func(t *testing.T, c *Config) {
				if len(c.Secrets) != 1 {
					t.Errorf("Expected 1 secret group, got %d", len(c.Secrets))
				}
				if c.Secrets[0].OutputDir != "/secrets/app" {
					t.Errorf("Expected output_dir=/secrets/app, got %s", c.Secrets[0].OutputDir)
				}
				if len(c.Secrets[0].Values) != 2 {
					t.Errorf("Expected 2 values, got %d", len(c.Secrets[0].Values))
				}
				if c.Secrets[0].UID != nil {
					t.Errorf("Expected UID to be nil, got %d", *c.Secrets[0].UID)
				}
			},
		},
		{
			name: "valid config with uid",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/app",
						"values": ["app/secret1"],
						"uid": 1000
					}
				]
			}`,
			wantErr: false,
			validate: func(t *testing.T, c *Config) {
				if c.Secrets[0].UID == nil {
					t.Error("Expected UID to be set, got nil")
				} else if *c.Secrets[0].UID != 1000 {
					t.Errorf("Expected UID=1000, got %d", *c.Secrets[0].UID)
				}
			},
		},
		{
			name: "multiple groups with mixed uid settings",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/app",
						"values": ["app/secret1"],
						"uid": 1000
					},
					{
						"output_dir": "/secrets/db",
						"values": ["db/password"]
					},
					{
						"output_dir": "/secrets/cache",
						"values": ["cache/token"],
						"uid": 999
					}
				]
			}`,
			wantErr: false,
			validate: func(t *testing.T, c *Config) {
				if len(c.Secrets) != 3 {
					t.Errorf("Expected 3 secret groups, got %d", len(c.Secrets))
				}
				if c.Secrets[0].UID == nil || *c.Secrets[0].UID != 1000 {
					t.Error("Expected first group to have UID=1000")
				}
				if c.Secrets[1].UID != nil {
					t.Error("Expected second group to have nil UID")
				}
				if c.Secrets[2].UID == nil || *c.Secrets[2].UID != 999 {
					t.Error("Expected third group to have UID=999")
				}
			},
		},
		{
			name: "uid zero is valid",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/root",
						"values": ["root/secret"],
						"uid": 0
					}
				]
			}`,
			wantErr: false,
			validate: func(t *testing.T, c *Config) {
				if c.Secrets[0].UID == nil || *c.Secrets[0].UID != 0 {
					t.Error("Expected UID=0 (root)")
				}
			},
		},
		{
			name: "invalid json",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/app"
						"values": ["app/secret1"]
					}
				]
			}`,
			wantErr:     true,
			errContains: "failed to parse JSON",
		},
		{
			name:       "empty config",
			configJSON: `{}`,
			wantErr:    false,
			validate: func(t *testing.T, c *Config) {
				if len(c.Secrets) != 0 {
					t.Errorf("Expected 0 secret groups, got %d", len(c.Secrets))
				}
			},
		},
		{
			name: "negative uid",
			configJSON: `{
				"secrets": [
					{
						"output_dir": "/secrets/app",
						"values": ["app/secret1"],
						"uid": -1
					}
				]
			}`,
			wantErr: false,
			validate: func(t *testing.T, c *Config) {
				if c.Secrets[0].UID == nil || *c.Secrets[0].UID != -1 {
					t.Error("Expected UID=-1 (will keep existing ownership)")
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temporary config file
			configPath := filepath.Join(tmpDir, "config.json")
			if err := os.WriteFile(configPath, []byte(tt.configJSON), 0600); err != nil {
				t.Fatalf("Failed to create test config file: %v", err)
			}
			defer os.Remove(configPath)

			// Load the configuration
			config, err := loadConfig(configPath)

			// Check error expectations
			if tt.wantErr {
				if err == nil {
					t.Error("Expected error, got nil")
				} else if tt.errContains != "" && !contains(err.Error(), tt.errContains) {
					t.Errorf("Expected error containing %q, got %q", tt.errContains, err.Error())
				}
				return
			}

			if err != nil {
				t.Fatalf("Unexpected error: %v", err)
			}

			// Run validation function if provided
			if tt.validate != nil {
				tt.validate(t, config)
			}
		})
	}
}

// TestConfigValidation tests the validation logic
func TestConfigValidation(t *testing.T) {
	uid1000 := 1000

	tests := []struct {
		name        string
		config      *Config
		wantErr     bool
		errContains string
	}{
		{
			name: "valid config",
			config: &Config{
				Secrets: []SecretGroup{
					{
						OutputDir: "/secrets/app",
						Values:    []string{"app/secret1"},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "valid config with uid",
			config: &Config{
				Secrets: []SecretGroup{
					{
						OutputDir: "/secrets/app",
						Values:    []string{"app/secret1"},
						UID:       &uid1000,
					},
				},
			},
			wantErr: false,
		},
		{
			name:        "empty secrets array",
			config:      &Config{Secrets: []SecretGroup{}},
			wantErr:     true,
			errContains: "at least one secret group",
		},
		{
			name: "empty output_dir",
			config: &Config{
				Secrets: []SecretGroup{
					{
						OutputDir: "",
						Values:    []string{"app/secret1"},
					},
				},
			},
			wantErr:     true,
			errContains: "output_dir cannot be empty",
		},
		{
			name: "empty values array",
			config: &Config{
				Secrets: []SecretGroup{
					{
						OutputDir: "/secrets/app",
						Values:    []string{},
					},
				},
			},
			wantErr:     true,
			errContains: "must have at least one value",
		},
		{
			name: "empty value string",
			config: &Config{
				Secrets: []SecretGroup{
					{
						OutputDir: "/secrets/app",
						Values:    []string{"app/secret1", ""},
					},
				},
			},
			wantErr:     true,
			errContains: "secret name cannot be empty",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.config.validate()

			if tt.wantErr {
				if err == nil {
					t.Error("Expected error, got nil")
				} else if tt.errContains != "" && !contains(err.Error(), tt.errContains) {
					t.Errorf("Expected error containing %q, got %q", tt.errContains, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
			}
		})
	}
}

// TestJSONMarshaling tests that configs can be marshaled and unmarshaled correctly
func TestJSONMarshaling(t *testing.T) {
	uid1000 := 1000
	uid999 := 999

	config := &Config{
		Secrets: []SecretGroup{
			{
				OutputDir: "/secrets/app",
				Values:    []string{"app/secret1", "app/secret2"},
				UID:       &uid1000,
			},
			{
				OutputDir: "/secrets/db",
				Values:    []string{"db/password"},
			},
			{
				OutputDir: "/secrets/cache",
				Values:    []string{"cache/token"},
				UID:       &uid999,
			},
		},
	}

	// Marshal to JSON
	jsonData, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal config: %v", err)
	}

	// Unmarshal back
	var parsed Config
	if err := json.Unmarshal(jsonData, &parsed); err != nil {
		t.Fatalf("Failed to unmarshal config: %v", err)
	}

	// Verify structure
	if len(parsed.Secrets) != 3 {
		t.Errorf("Expected 3 secret groups, got %d", len(parsed.Secrets))
	}

	// Verify first group (with UID)
	if parsed.Secrets[0].UID == nil {
		t.Error("Expected first group to have UID set")
	} else if *parsed.Secrets[0].UID != 1000 {
		t.Errorf("Expected UID=1000, got %d", *parsed.Secrets[0].UID)
	}

	// Verify second group (without UID)
	if parsed.Secrets[1].UID != nil {
		t.Errorf("Expected second group to have nil UID, got %d", *parsed.Secrets[1].UID)
	}

	// Verify third group (with UID)
	if parsed.Secrets[2].UID == nil {
		t.Error("Expected third group to have UID set")
	} else if *parsed.Secrets[2].UID != 999 {
		t.Errorf("Expected UID=999, got %d", *parsed.Secrets[2].UID)
	}
}

// Helper function to check if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		(len(s) > 0 && len(substr) > 0 && containsHelper(s, substr)))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
