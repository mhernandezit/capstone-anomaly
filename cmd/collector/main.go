package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"time"

	api "github.com/osrg/gobgp/v3/api"
	"github.com/osrg/gobgp/v3/pkg/server"
	"github.com/nats-io/nats.go"
	"gopkg.in/yaml.v3"
)

type PeerCfg struct {
	Address  string `yaml:"address"`
	RemoteAS uint32 `yaml:"remote_as"`
	Passive  bool   `yaml:"passive"`
}

type Cfg struct {
	ASN      uint32    `yaml:"asn"`
	RouterID string    `yaml:"router_id"`
	BindAddr string    `yaml:"bind_addr"`
	Peers    []PeerCfg `yaml:"peers"`
	NATS     struct {
		URL     string `yaml:"url"`
		Subject string `yaml:"subject"`
	} `yaml:"nats"`
}

type BGPUpdate struct {
	Timestamp int64          `json:"ts"`
	Peer      string         `json:"peer"`
	MsgType   string         `json:"type"` // UPDATE, KEEPALIVE, NOTIFICATION
	Announce  []string       `json:"announce,omitempty"`
	Withdraw  []string       `json:"withdraw,omitempty"`
	Attrs     map[string]any `json:"attrs,omitempty"`
}

func must[T any](v T, err error) T {
	if err != nil {
		log.Fatal(err)
	}
	return v
}

func main() {
	cfgBytes := must(os.ReadFile("configs/collector.yml"))
	var cfg Cfg
	must(0, yaml.Unmarshal(cfgBytes, &cfg))

	nc := must(nats.Connect(cfg.NATS.URL))
	defer nc.Drain()

	s := server.NewBgpServer()
	go s.Serve()

	global := &api.Global{
		Asn:             cfg.ASN,
		RouterId:        cfg.RouterID,
		ListenAddresses: []string{cfg.BindAddr},
	}
	must(0, s.StartBgp(context.Background(), &api.StartBgpRequest{Global: global}))

	for _, p := range cfg.Peers {
		peer := &api.Peer{
			Conf: &api.PeerConf{
				NeighborAddress: p.Address,
				PeerAsn:         p.RemoteAS,
			},
			Transport: &api.Transport{
				PassiveMode: p.Passive,
			},
		}
		must(0, s.AddPeer(context.Background(), &api.AddPeerRequest{Peer: peer}))
	}

	// Simple message simulation since Watch API is complex in v3
	// In production, you'd use the proper Watch API or BMP
	log.Println("BGP Collector started. In a real implementation, this would watch for BGP updates.")
	log.Printf("Configured peers: %d", len(cfg.Peers))
	log.Printf("Publishing to NATS subject: %s", cfg.NATS.Subject)
	
	// Simulate a test message every 30 seconds for development
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for range ticker.C {
		testUpdate := BGPUpdate{
			Timestamp: time.Now().Unix(),
			Peer:      "10.0.1.1",
			MsgType:   "UPDATE",
			Announce:  []string{"192.168.1.0/24"},
			Attrs:     map[string]any{"as_path_len": 3, "next_hop": "10.0.1.1"},
		}
		b := must(json.Marshal(testUpdate))
		err := nc.Publish(cfg.NATS.Subject, b)
		if err != nil {
			log.Printf("Error publishing to NATS: %v", err)
		}
		log.Printf("Published test BGP update: %s", string(b))
	}
}
