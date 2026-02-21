package setec

import (
	"context"

	tailscale_setec "github.com/tailscale/setec/client/setec"
)

func LoadSecret(secret_name string) (string, error) {
	client := tailscale_setec.Client{Server: "https://setec.barn-arcturus.ts.net"}
	auth, err := client.Get(context.Background(), secret_name)
	return string(auth.Value), err
}
