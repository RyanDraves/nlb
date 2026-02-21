package util

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

var (
	infoStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("117")) // Light Blue
	errorStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("196")) // Red
	warningStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("226")) // Yellow
	successStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("46"))  // Green
)

func Info(msg string, args ...any) {
	formatted := fmt.Sprintf(msg, args...)
	fmt.Println(infoStyle.Render(formatted))
}

func Error(msg string, args ...any) {
	formatted := fmt.Sprintf(msg, args...)
	fmt.Println(errorStyle.Render(formatted))
}

func Warning(msg string, args ...any) {
	formatted := fmt.Sprintf(msg, args...)
	fmt.Println(warningStyle.Render(formatted))
}

func Success(msg string, args ...any) {
	formatted := fmt.Sprintf(msg, args...)
	fmt.Println(successStyle.Render(formatted))
}

func Print(msg string, args ...any) {
	fmt.Printf(msg, args...)
}

// NewError creates a new formatted error
func NewError(msg string, args ...any) error {
	return fmt.Errorf(msg, args...)
}
