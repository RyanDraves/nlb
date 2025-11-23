package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"
)

const usage = `docker_secret_injector - Inject secrets from files into environment variables

DESCRIPTION:
    This tool scans environment variables for those ending in "_PATH", reads the
    contents of the files they point to, and sets corresponding environment variables
    without the "_PATH" suffix. It then executes a specified command as a child
    process with the updated environment.

    This is particularly useful in Docker environments where secrets are mounted as
    files (e.g., Docker secrets, Kubernetes secrets) and need to be converted to
    environment variables for applications that expect them.

USAGE:
    docker_secret_injector [OPTIONS] -- COMMAND [ARGS...]

OPTIONS:
    -verbose
        Print verbose output showing which secrets were injected.

    -help
        Show this help message.

EXAMPLES:
    # Inject all *_PATH environment variables and run env
    docker_secret_injector -- env

    # Inject some key and run some binary
    export MY_KEY_PATH=/run/secrets/my_key
    docker_secret_injector -verbose -- some_binary

ENVIRONMENT VARIABLE MAPPING:
    Input Env Var                 File Path           Output Env Var
    ──────────────────────────────────────────────────────────────────
    MY_KEY_PATH=/run/secrets/my_key           → MY_KEY=<file contents>
    DB_SECRET_PATH=/run/secrets/db_secret     → DB_SECRET=<file contents>

NOTES:
    - File contents are automatically trimmed of leading/trailing whitespace
    - If a file cannot be read, a warning is logged but execution continues
    - The original *_PATH variables remain in the environment
    - Runs the command as a child process and forwards signals
    - Exits with the same exit code as the child process
`

func main() {
	var (
		verbose = flag.Bool("verbose", false, "Print verbose output")
		help    = flag.Bool("help", false, "Show help message")
	)

	// Custom usage function
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "%s", usage)
	}

	flag.Parse()

	if *help {
		flag.Usage()
		os.Exit(0)
	}

	// Get the command to execute (everything after --)
	args := flag.Args()
	if len(args) == 0 {
		log.Fatal("Error: no command specified. Use -- to separate options from the command.\nRun with -help for usage information.")
	}

	// Process all environment variables
	injectSecretsFromPaths(*verbose)

	// Create the command with injected environment
	cmd := exec.Command(args[0], args[1:]...)
	cmd.Env = os.Environ()
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if *verbose {
		log.Printf("Executing: %s [hidden args]", args[0])
	}

	// Set up signal forwarding to child process
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start the command
	if err := cmd.Start(); err != nil {
		log.Fatalf("Failed to start %q: %v", args[0], err)
	}

	// Forward signals to child process
	go func() {
		for sig := range sigChan {
			if cmd.Process != nil {
				cmd.Process.Signal(sig)
			}
		}
	}()

	// Wait for the command to complete
	if err := cmd.Wait(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			// Exit with the same code as the child process
			os.Exit(exitErr.ExitCode())
		}
		log.Fatalf("Command failed: %v", err)
	}
}

// injectSecretsFromPaths scans environment variables for those ending in "_PATH",
// reads the file contents, and sets the corresponding variable without the "_PATH" suffix.
func injectSecretsFromPaths(verbose bool) {
	const pathSuffix = "_PATH"
	var injected []string

	for _, env := range os.Environ() {
		// Parse the environment variable
		parts := strings.SplitN(env, "=", 2)
		if len(parts) != 2 {
			continue
		}

		envName := parts[0]
		envValue := parts[1]

		// Check if this variable ends with _PATH
		if !strings.HasSuffix(envName, pathSuffix) {
			continue
		}

		// Skip if the file path is empty
		if envValue == "" {
			if verbose {
				log.Printf("Skipping %s: empty path", envName)
			}
			continue
		}

		// Read the file contents
		data, err := os.ReadFile(envValue)
		if err != nil && verbose {
			log.Printf("Warning: failed to read %s from %q: %v", envName, envValue, err)
			continue
		}

		// Trim whitespace from the file contents
		secretValue := strings.TrimSpace(string(data))

		// Calculate the target environment variable name (remove _PATH suffix)
		targetEnvName := strings.TrimSuffix(envName, pathSuffix)

		// Set the environment variable
		if err := os.Setenv(targetEnvName, secretValue); err != nil {
			log.Printf("Warning: failed to set %s: %v", targetEnvName, err)
			continue
		}

		injected = append(injected, targetEnvName)
	}

	if verbose && len(injected) > 0 {
		log.Printf("Injected %d secret(s) from files", len(injected))
		for _, name := range injected {
			log.Printf("  ✓ %s", name)
		}
	}
}
