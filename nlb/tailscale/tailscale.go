package tailscale

import (
	"context"
	"io"
	"nlb/nlb/util"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"tailscale.com/client/local"
	"tailscale.com/client/tailscale/apitype"
	"tailscale.com/ipn/ipnstate"
	"tailscale.com/tailcfg"
)

type PeerFilter int

const (
	PeerFilterAny PeerFilter = iota
	PeerFilterOnlineOnly
	PeerFilterTaildropOnly
)

// TailscaleClient defines the interface for Tailscale client operations
type TailscaleClient interface {
	Status(ctx context.Context) (*ipnstate.Status, error)
	PushFile(ctx context.Context, peerID tailcfg.StableNodeID, size int64, name string, r io.Reader) error
	WaitingFiles(ctx context.Context) ([]apitype.WaitingFile, error)
	GetWaitingFile(ctx context.Context, baseName string) (io.ReadCloser, int64, error)
}

type TailscaleWrapper struct {
	LocalClient TailscaleClient
	ctx         context.Context
}

func NewTailscaleWrapper() (*TailscaleWrapper, error) {
	return &TailscaleWrapper{
		LocalClient: &local.Client{},
		ctx:         context.Background(),
	}, nil
}

func (w *TailscaleWrapper) ListPeers(filter PeerFilter) ([]*ipnstate.PeerStatus, error) {
	status, err := w.LocalClient.Status(w.ctx)
	if err != nil {
		return nil, err
	}

	peers := make([]*ipnstate.PeerStatus, 0)

	for _, peer := range status.Peer {
		if filter == PeerFilterAny {
			peers = append(peers, peer)
		} else if filter == PeerFilterTaildropOnly && peer.TaildropTarget == ipnstate.TaildropTargetAvailable {
			peers = append(peers, peer)
		} else if filter == PeerFilterOnlineOnly && peer.Online {
			peers = append(peers, peer)
		}
	}

	return peers, nil
}

func (w *TailscaleWrapper) PrintPeers() error {
	peers, err := w.ListPeers(PeerFilterOnlineOnly)
	if err != nil {
		return err
	}

	util.Info("Peers connected to the network:")
	for _, peer := range peers {
		util.Info("  - %s", strings.Split(peer.DNSName, ".")[0])
	}

	return nil
}

func (w *TailscaleWrapper) promptForPeer() (*ipnstate.PeerStatus, error) {
	peers, err := w.ListPeers(PeerFilterTaildropOnly)
	if err != nil {
		return nil, err
	}

	return util.ListPrompt(
		"Select a peer",
		peers,
		func(p *ipnstate.PeerStatus) string {
			return strings.Split(p.DNSName, ".")[0]
		},
	)
}

func (w *TailscaleWrapper) promptForFiles() ([]string, error) {
	return util.PromptForFiles("Select a file:")
}

func (w *TailscaleWrapper) SendFiles() error {
	peer, err := w.promptForPeer()
	if err != nil {
		return err
	}

	files, err := w.promptForFiles()
	if err != nil {
		return err
	}

	for _, file := range files {
		file_info, err := os.Stat(file)
		if err != nil {
			util.Error("Failed to stat file %s: %v", file, err)
			return err
		}
		file_size := file_info.Size()
		file_name := file_info.Name()
		file_reader, err := os.Open(file)
		if err != nil {
			util.Error("Failed to open file %s: %v", file, err)
			return err
		}
		defer file_reader.Close()

		err = w.LocalClient.PushFile(w.ctx, peer.ID, file_size, file_name, file_reader)
		if err != nil {
			util.Error("Failed to send file %s to peer %s: %v", file, strings.Split(peer.DNSName, ".")[0], err)
			return err
		}
	}

	return nil
}

func (w *TailscaleWrapper) promptForDirectory() (string, error) {
	return util.PromptForDirectory("Select a directory:")
}

func (w *TailscaleWrapper) ReceiveFiles() error {
	waiting_files, err := w.LocalClient.WaitingFiles(w.ctx)
	if err != nil {
		return err
	}

	if len(waiting_files) == 0 {
		util.Info("No files waiting to be received")
		return nil
	}

	directory, err := w.promptForDirectory()
	if err != nil {
		return err
	}

	for _, file := range waiting_files {
		// Copy the file to the selected directory
		rc, _, err := w.LocalClient.GetWaitingFile(w.ctx, file.Name)
		if err != nil {
			util.Error("Failed to get file %s: %v", file.Name, err)
			return err
		}
		defer rc.Close()

		file_path := directory + "/" + file.Name
		file_writer, err := os.Create(file_path)
		if err != nil {
			util.Error("Failed to create file %s: %v", file_path, err)
			return err
		}
		defer file_writer.Close()

		_, err = file_writer.ReadFrom(rc)
		if err != nil {
			util.Error("Failed to copy file %s: %v", file.Name, err)
			return err
		}

		util.Info("Received file: %s", file_path)
	}

	return nil
}

type fileWithTime struct {
	path    string
	modTime time.Time
}

func (w *TailscaleWrapper) promptForScreenshots(hoursAgo int) ([]string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}
	screenshotDir := filepath.Join(homeDir, "Pictures", "Screenshots")

	// Get all files in screenshot directory recursively
	var filesWithTime []fileWithTime
	err = filepath.Walk(screenshotDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			filesWithTime = append(filesWithTime, fileWithTime{
				path:    path,
				modTime: info.ModTime(),
			})
		}
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Sort by modification time (most recent first)
	sort.Slice(filesWithTime, func(i, j int) bool {
		return filesWithTime[i].modTime.After(filesWithTime[j].modTime)
	})

	// Filter for files modified in the last hoursAgo hours
	now := time.Now()
	cutoff := now.Add(-time.Duration(hoursAgo) * time.Hour)
	var recentFiles []fileWithTime
	for _, f := range filesWithTime {
		if f.modTime.After(cutoff) {
			recentFiles = append(recentFiles, f)
		}
	}

	// Fallback: 5 most recent screenshots if no recent files
	if len(recentFiles) == 0 {
		if len(filesWithTime) > 5 {
			recentFiles = filesWithTime[:5]
		} else {
			recentFiles = filesWithTime
		}
	}

	if len(recentFiles) == 0 {
		return nil, util.NewError("No screenshots found")
	}

	// Prompt for multi-select with relative paths
	selectedFiles, err := util.MultiSelectPrompt(
		"Select screenshots to send",
		recentFiles,
		func(f fileWithTime) string {
			relPath, _ := filepath.Rel(screenshotDir, f.path)
			return relPath
		},
	)
	if err != nil {
		return nil, err
	}

	// Extract just the paths
	paths := make([]string, len(selectedFiles))
	for i, f := range selectedFiles {
		paths[i] = f.path
	}

	return paths, nil
}

func (w *TailscaleWrapper) SendScreenshots(hoursAgo int) error {
	peer, err := w.promptForPeer()
	if err != nil {
		return err
	}

	files, err := w.promptForScreenshots(hoursAgo)
	if err != nil {
		return err
	}

	for _, file := range files {
		file_info, err := os.Stat(file)
		if err != nil {
			util.Error("Failed to stat file %s: %v", file, err)
			return err
		}
		file_size := file_info.Size()
		file_name := file_info.Name()
		file_reader, err := os.Open(file)
		if err != nil {
			util.Error("Failed to open file %s: %v", file, err)
			return err
		}
		defer file_reader.Close()

		err = w.LocalClient.PushFile(w.ctx, peer.ID, file_size, file_name, file_reader)
		if err != nil {
			util.Error("Failed to send file %s to peer %s: %v", file, strings.Split(peer.DNSName, ".")[0], err)
			return err
		}
	}

	filesStr := "Files"
	if len(files) == 1 {
		filesStr = "File"
	}
	util.Success("%s sent successfully", filesStr)

	return nil
}
