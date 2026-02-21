package util

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/filepicker"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type listModel[T any] struct {
	message     string
	items       []T
	displayFunc func(T) string
	cursor      int
	selected    *T
	done        bool
}

func (m listModel[T]) Init() tea.Cmd {
	return nil
}

func (m listModel[T]) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.items)-1 {
				m.cursor++
			}
		case "enter":
			m.selected = &m.items[m.cursor]
			m.done = true
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m listModel[T]) View() string {
	if m.done && m.selected != nil {
		// Collapsed view after selection
		selectedName := m.displayFunc(*m.selected)
		selectedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
		return fmt.Sprintf("? %s: %s\n", m.message, selectedStyle.Render(selectedName))
	}

	// Full interactive view
	s := m.message + ":\n\n"

	cursorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))

	for i, item := range m.items {
		cursor := " "
		name := m.displayFunc(item)
		if m.cursor == i {
			cursor = ">"
			name = cursorStyle.Render(name)
		}
		s += fmt.Sprintf("%s %s\n", cursor, name)
	}

	s += "\n(use arrows or j/k to move, enter to select, q to quit)\n"
	return s
}

// ListPrompt displays an interactive list selection prompt and returns the selected item.
// The displayFunc parameter converts each item to a string for display purposes.
func ListPrompt[T any](message string, items []T, displayFunc func(T) string) (T, error) {
	var zero T
	if len(items) == 0 {
		return zero, fmt.Errorf("no items available")
	}

	model := listModel[T]{
		message:     message,
		items:       items,
		displayFunc: displayFunc,
		cursor:      0,
	}

	p := tea.NewProgram(model)
	result, err := p.Run()
	if err != nil {
		return zero, err
	}

	finalModel := result.(listModel[T])
	if finalModel.selected == nil {
		return zero, fmt.Errorf("no item selected")
	}

	return *finalModel.selected, nil
}

type multiSelectModel[T any] struct {
	message     string
	items       []T
	displayFunc func(T) string
	cursor      int
	selected    map[int]bool
	done        bool
}

func (m multiSelectModel[T]) Init() tea.Cmd {
	return nil
}

func (m multiSelectModel[T]) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q", "esc":
			m.done = true
			m.selected = nil
			return m, tea.Quit
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.items)-1 {
				m.cursor++
			}
		case " ":
			// Toggle selection
			if m.selected[m.cursor] {
				delete(m.selected, m.cursor)
			} else {
				m.selected[m.cursor] = true
			}
		case "enter":
			m.done = true
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m multiSelectModel[T]) View() string {
	if m.done {
		// Collapsed view after selection
		selectedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
		selectedNames := []string{}
		for i := range m.selected {
			selectedNames = append(selectedNames, m.displayFunc(m.items[i]))
		}
		return fmt.Sprintf("? %s: %s\n", m.message, selectedStyle.Render(fmt.Sprintf("%d selected", len(selectedNames))))
	}

	// Full interactive view
	s := m.message + ":\n\n"

	cursorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
	uncheckedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	checkedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86")).Bold(true)

	for i, item := range m.items {
		cursor := " "
		checkbox := uncheckedStyle.Render("◯")
		name := m.displayFunc(item)

		if m.selected[i] {
			checkbox = checkedStyle.Render("◉")
		}

		if m.cursor == i {
			cursor = cursorStyle.Render(">")
			name = cursorStyle.Render(name)
		}

		s += fmt.Sprintf("%s %s %s\n", cursor, checkbox, name)
	}

	s += "\n(use arrows or j/k to move, space to toggle, enter to confirm, q to quit)\n"
	return s
}

// MultiSelectPrompt displays an interactive multi-select list prompt and returns the selected items.
// The displayFunc parameter converts each item to a string for display purposes.
func MultiSelectPrompt[T any](message string, items []T, displayFunc func(T) string) ([]T, error) {
	if len(items) == 0 {
		return nil, fmt.Errorf("no items available")
	}

	model := multiSelectModel[T]{
		message:     message,
		items:       items,
		displayFunc: displayFunc,
		cursor:      0,
		selected:    make(map[int]bool),
	}

	p := tea.NewProgram(model)
	result, err := p.Run()
	if err != nil {
		return nil, err
	}

	finalModel := result.(multiSelectModel[T])
	if finalModel.selected == nil {
		return nil, fmt.Errorf("cancelled")
	}
	if len(finalModel.selected) == 0 {
		return nil, fmt.Errorf("no items selected")
	}

	selectedItems := make([]T, 0, len(finalModel.selected))
	for i := range finalModel.selected {
		selectedItems = append(selectedItems, finalModel.items[i])
	}

	return selectedItems, nil
}

type filePathModel struct {
	textInput textinput.Model
	message   string
	value     string
	done      bool
	err       error
}

func (m filePathModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m filePathModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyEnter:
			m.value = m.textInput.Value()
			m.done = true
			return m, tea.Quit
		case tea.KeyCtrlC, tea.KeyEsc:
			m.err = fmt.Errorf("cancelled")
			return m, tea.Quit
		}
	}

	m.textInput, cmd = m.textInput.Update(msg)
	return m, cmd
}

func (m filePathModel) View() string {
	if m.done {
		// Collapsed view after completion
		selectedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
		return fmt.Sprintf("? %s: %s\n", m.message, selectedStyle.Render(m.value))
	}

	return fmt.Sprintf(
		"%s:\n\n%s\n\n(enter to confirm, ctrl+c to cancel)\n",
		m.message,
		m.textInput.View(),
	)
}

// FilePathPrompt displays a text input prompt for entering a file path or glob pattern.
// Returns the user's input string.
func FilePathPrompt(message string, defaultValue string) (string, error) {
	ti := textinput.New()
	ti.Placeholder = defaultValue
	ti.Focus()
	ti.CharLimit = 500
	ti.Width = 50

	if defaultValue != "" {
		ti.SetValue(defaultValue)
	}

	model := filePathModel{
		textInput: ti,
		message:   message,
	}

	p := tea.NewProgram(model)
	result, err := p.Run()
	if err != nil {
		return "", err
	}

	finalModel := result.(filePathModel)
	if finalModel.err != nil {
		return "", finalModel.err
	}

	return finalModel.value, nil
}

type filePickerModel struct {
	filepicker   filepicker.Model
	header       string
	selectedFile string
	done         bool
	err          error
}

type clearErrorMsg struct{}

func clearErrorAfter() tea.Cmd {
	return tea.Tick(time.Second*2, func(_ time.Time) tea.Msg {
		return clearErrorMsg{}
	})
}

func (m filePickerModel) Init() tea.Cmd {
	return m.filepicker.Init()
}

func (m filePickerModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			m.err = fmt.Errorf("cancelled")
			return m, tea.Quit
		}
	case clearErrorMsg:
		m.err = nil
	}

	var cmd tea.Cmd
	m.filepicker, cmd = m.filepicker.Update(msg)

	if didSelect, path := m.filepicker.DidSelectFile(msg); didSelect {
		m.selectedFile = path
		m.done = true
		return m, tea.Quit
	}

	return m, cmd
}

func (m filePickerModel) View() string {
	if m.done {
		// Collapsed view after selection
		selectedStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
		return fmt.Sprintf("? Select a file or glob pattern: %s\n", selectedStyle.Render(m.selectedFile))
	}

	var s strings.Builder
	s.WriteString("\n  ")
	if m.err != nil {
		s.WriteString(m.filepicker.Styles.DisabledFile.Render(m.err.Error()))
	} else {
		s.WriteString(m.header)
	}
	s.WriteString("\n" + m.filepicker.CurrentDirectory + "/" + m.filepicker.FileSelected)
	s.WriteString("\n" + m.filepicker.View() + "\n")
	return s.String()
}

// PromptForFiles prompts with an interactive file browser and returns matching files.
func PromptForFiles(message string) ([]string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		cwd = "."
	}

	fp := filepicker.New()
	fp.CurrentDirectory = cwd
	fp.ShowHidden = true
	fp.ShowPermissions = false
	fp.DirAllowed = true
	fp.FileAllowed = true

	model := filePickerModel{
		filepicker: fp,
		header:     message,
	}

	p := tea.NewProgram(model)
	result, err := p.Run()
	if err != nil {
		return nil, err
	}

	finalModel := result.(filePickerModel)
	if finalModel.err != nil {
		return nil, finalModel.err
	}

	path := finalModel.selectedFile

	// Check if the path is a directory
	info, err := os.Stat(path)
	if err == nil && info.IsDir() {
		path = filepath.Join(path, "*")
	}

	// Expand glob pattern if it contains wildcards
	if strings.ContainsAny(path, "*?[]") {
		matches, err := filepath.Glob(path)
		if err != nil {
			return nil, fmt.Errorf("invalid glob pattern: %w", err)
		}

		// Filter to only files
		files := []string{}
		for _, match := range matches {
			info, err := os.Stat(match)
			if err == nil && !info.IsDir() {
				files = append(files, match)
			}
		}

		if len(files) == 0 {
			return nil, fmt.Errorf("no files matched pattern: %s", path)
		}
		return files, nil
	}

	// Single file selected
	return []string{path}, nil
}

// PromptForDirectory prompts with an interactive file browser and returns the selected directory path
func PromptForDirectory(message string) (string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		cwd = "."
	}

	fp := filepicker.New()
	fp.CurrentDirectory = cwd
	fp.ShowHidden = false
	fp.ShowPermissions = false
	fp.DirAllowed = true
	fp.FileAllowed = false

	model := filePickerModel{
		filepicker: fp,
		header:     message,
	}

	p := tea.NewProgram(model)
	result, err := p.Run()
	if err != nil {
		return "", err
	}

	finalModel := result.(filePickerModel)
	if finalModel.err != nil {
		return "", finalModel.err
	}

	return finalModel.selectedFile, nil
}
