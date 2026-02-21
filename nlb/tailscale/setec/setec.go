package setec

import (
	"context"

	tailscale_setec "github.com/tailscale/setec/client/setec"
)

func LoadSecret(secret_name, server string) (string, error) {
	serverURL := server
	if serverURL == "" {
		serverURL = "https://setec.barn-arcturus.ts.net"
	}
	client := tailscale_setec.Client{Server: serverURL}
	auth, err := client.Get(context.Background(), secret_name)
	return string(auth.Value), err
}
