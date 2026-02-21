package main

import (
	"log"
	"os"

	"nlb/nlb/tailscale"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "nlb_tailscale",
	Short: "Tailscale CLI wrapper",
	Long:  "A CLI wrapper around the Tailscale API for common operations",
}

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List peers connected to the network",
	RunE: func(cmd *cobra.Command, args []string) error {
		wrapper, err := tailscale.NewTailscaleWrapper()
		if err != nil {
			return err
		}
		return wrapper.PrintPeers()
	},
}

var sendCmd = &cobra.Command{
	Use:   "send",
	Short: "Send files to a peer",
	RunE: func(cmd *cobra.Command, args []string) error {
		wrapper, err := tailscale.NewTailscaleWrapper()
		if err != nil {
			return err
		}
		return wrapper.SendFiles()
	},
}

var sendScreenshotCmd = &cobra.Command{
	Use:   "send-screenshot",
	Short: "Send recent screenshots to a peer",
	RunE: func(cmd *cobra.Command, args []string) error {
		wrapper, err := tailscale.NewTailscaleWrapper()
		if err != nil {
			return err
		}
		hoursAgo, _ := cmd.Flags().GetInt("hours")
		return wrapper.SendScreenshots(hoursAgo)
	},
}

var receiveCmd = &cobra.Command{
	Use:   "receive",
	Short: "Receive files from peers",
	RunE: func(cmd *cobra.Command, args []string) error {
		wrapper, err := tailscale.NewTailscaleWrapper()
		if err != nil {
			return err
		}
		return wrapper.ReceiveFiles()
	},
}

func init() {
	sendScreenshotCmd.Flags().IntP("hours", "H", 1, "Filter screenshots from the last N hours")

	rootCmd.AddCommand(listCmd)
	rootCmd.AddCommand(sendCmd)
	rootCmd.AddCommand(sendScreenshotCmd)
	rootCmd.AddCommand(receiveCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		log.Fatal(err)
		os.Exit(1)
	}
}
