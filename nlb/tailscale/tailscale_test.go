package tailscale

import (
	"bytes"
	"context"
	"io"
	"testing"

	"tailscale.com/client/tailscale/apitype"
	"tailscale.com/ipn/ipnstate"
	"tailscale.com/tailcfg"
	"tailscale.com/types/key"
)

// mockTailscaleClient implements TailscaleClient for testing
type mockTailscaleClient struct {
	status       *ipnstate.Status
	statusErr    error
	pushFileErr  error
	waitingFiles []apitype.WaitingFile
	waitingErr   error
	fileContents map[string]string
}

func (m *mockTailscaleClient) Status(ctx context.Context) (*ipnstate.Status, error) {
	if m.statusErr != nil {
		return nil, m.statusErr
	}
	return m.status, nil
}

func (m *mockTailscaleClient) PushFile(ctx context.Context, peerID tailcfg.StableNodeID, size int64, name string, r io.Reader) error {
	return m.pushFileErr
}

func (m *mockTailscaleClient) WaitingFiles(ctx context.Context) ([]apitype.WaitingFile, error) {
	if m.waitingErr != nil {
		return nil, m.waitingErr
	}
	return m.waitingFiles, nil
}

func (m *mockTailscaleClient) GetWaitingFile(ctx context.Context, baseName string) (io.ReadCloser, int64, error) {
	content, ok := m.fileContents[baseName]
	if !ok {
		content = "test file content"
	}
	return io.NopCloser(bytes.NewBufferString(content)), int64(len(content)), nil
}

func TestListPeers(t *testing.T) {
	// Create unique keys for each peer
	key1 := key.NewNode()
	key2 := key.NewNode()
	key3 := key.NewNode()

	tests := []struct {
		name          string
		filter        PeerFilter
		mockStatus    *ipnstate.Status
		expectedCount int
		expectError   bool
	}{
		{
			name:   "filter online only",
			filter: PeerFilterOnlineOnly,
			mockStatus: &ipnstate.Status{
				Peer: map[key.NodePublic]*ipnstate.PeerStatus{
					key1.Public(): {
						DNSName: "peer1.example.ts.net",
						Online:  true,
					},
					key2.Public(): {
						DNSName: "peer2.example.ts.net",
						Online:  false,
					},
					key3.Public(): {
						DNSName: "peer3.example.ts.net",
						Online:  true,
					},
				},
			},
			expectedCount: 2,
			expectError:   false,
		},
		{
			name:   "filter taildrop only",
			filter: PeerFilterTaildropOnly,
			mockStatus: &ipnstate.Status{
				Peer: map[key.NodePublic]*ipnstate.PeerStatus{
					key1.Public(): {
						DNSName:        "peer1.example.ts.net",
						TaildropTarget: ipnstate.TaildropTargetAvailable,
					},
					key2.Public(): {
						DNSName:        "peer2.example.ts.net",
						TaildropTarget: ipnstate.TaildropTargetUnsupportedOS,
					},
				},
			},
			expectedCount: 1,
			expectError:   false,
		},
		{
			name:   "filter any",
			filter: PeerFilterAny,
			mockStatus: &ipnstate.Status{
				Peer: map[key.NodePublic]*ipnstate.PeerStatus{
					key1.Public(): {
						DNSName: "peer1.example.ts.net",
						Online:  false,
					},
					key2.Public(): {
						DNSName: "peer2.example.ts.net",
						Online:  false,
					},
				},
			},
			expectedCount: 2,
			expectError:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			wrapper := &TailscaleWrapper{
				LocalClient: &mockTailscaleClient{
					status: tt.mockStatus,
				},
				ctx: context.Background(),
			}

			peers, err := wrapper.ListPeers(tt.filter)

			if tt.expectError && err == nil {
				t.Error("expected error, got nil")
			}
			if !tt.expectError && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
			if len(peers) != tt.expectedCount {
				t.Errorf("expected %d peers, got %d", tt.expectedCount, len(peers))
			}
		})
	}
}

func TestListPeers_EmptyPeers(t *testing.T) {
	wrapper := &TailscaleWrapper{
		LocalClient: &mockTailscaleClient{
			status: &ipnstate.Status{
				Peer: map[key.NodePublic]*ipnstate.PeerStatus{},
			},
		},
		ctx: context.Background(),
	}

	peers, err := wrapper.ListPeers(PeerFilterAny)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if len(peers) != 0 {
		t.Errorf("expected 0 peers, got %d", len(peers))
	}
}

func TestPrintPeers(t *testing.T) {
	wrapper := &TailscaleWrapper{
		LocalClient: &mockTailscaleClient{
			status: &ipnstate.Status{
				Peer: map[key.NodePublic]*ipnstate.PeerStatus{
					{}: {
						DNSName: "test-peer.example.ts.net",
						Online:  true,
					},
				},
			},
		},
		ctx: context.Background(),
	}

	err := wrapper.PrintPeers()
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
}
