package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/tailscale/setec/client/setec"
)

// Config represents the configuration file structure
type Config struct {
	Secrets []SecretGroup `json:"secrets"`
}

// SecretGroup represents a group of secrets to be written to a directory
type SecretGroup struct {
	OutputDir string   `json:"output_dir"`
	Values    []string `json:"values"`
}

// validate checks if the configuration is valid
func (c *Config) validate() error {
	if len(c.Secrets) == 0 {
		return fmt.Errorf("configuration must have at least one secret group")
	}

	for i, group := range c.Secrets {
		if group.OutputDir == "" {
			return fmt.Errorf("secret group %d: output_dir cannot be empty", i)
		}
		if len(group.Values) == 0 {
			return fmt.Errorf("secret group %d: must have at least one value", i)
		}
		for j, value := range group.Values {
			if value == "" {
				return fmt.Errorf("secret group %d, value %d: secret name cannot be empty", i, j)
			}
		}
	}

	return nil
}

func main() {
	configPath := flag.String("config", os.Getenv("SPIRIT_TRACKS_CONFIG"), "Path to configuration JSON file (env: SPIRIT_TRACKS_CONFIG)")
	setecAddr := flag.String("setec-addr", os.Getenv("SPIRIT_TRACKS_SETEC_ADDR"), "Address of the setec server (env: SPIRIT_TRACKS_SETEC_ADDR)")
	flag.Parse()

	if *configPath == "" {
		log.Fatal("--config flag or SPIRIT_TRACKS_CONFIG environment variable is required")
	}
	if *setecAddr == "" {
		log.Fatal("--setec-addr flag or SPIRIT_TRACKS_SETEC_ADDR environment variable is required")
	}

	// Load and parse configuration
	config, err := loadConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Validate configuration
	if err := config.validate(); err != nil {
		log.Fatalf("Invalid configuration: %v", err)
	}

	// Create setec client
	ctx := context.Background()
	client := setec.Client{Server: *setecAddr}

	// Process each secret group
	for i, group := range config.Secrets {
		log.Printf("Processing secret group %d: %s", i+1, group.OutputDir)

		// Retrieve and write each secret
		for _, secretName := range group.Values {
			if err := writeSecret(ctx, &client, group.OutputDir, secretName); err != nil {
				log.Fatalf("Failed to write secret %s: %v", secretName, err)
			}
			log.Printf("  ✓ Written secret: %s", secretName)
		}
	}

	log.Println("All secrets written successfully")
}

// loadConfig reads and parses the configuration file
func loadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	return &config, nil
}

// writeSecret retrieves a secret from setec and writes it to a file
func writeSecret(ctx context.Context, client *setec.Client, outputDir, secretName string) error {
	// Get the secret from setec
	secret, err := client.Get(ctx, secretName)
	if err != nil {
		return fmt.Errorf("failed to get secret from setec: %w", err)
	}

	// Sanitize the secret name for use as a filename (replace / with _)
	filename := strings.ReplaceAll(secretName, "/", "_")
	outputPath := filepath.Join(outputDir, filename)

	// Ensure output directory exists
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write secret to file with secure permissions (0600 = rw-------)
	if err := os.WriteFile(outputPath, []byte(secret.Value), 0600); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}
