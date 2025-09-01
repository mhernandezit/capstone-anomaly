package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"time"

	bgp "github.com/osrg/gobgp/v3/pkg/packet/bgp"
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

	global := &server.Global{
		As:              cfg.ASN,
		RouterId:        cfg.RouterID,
		ListenAddresses: []string{cfg.BindAddr},
	}
	must(0, s.StartBgp(context.Background(), &server.Bgp{Global: global}))

	for _, p := range cfg.Peers {
		pp := &server.Peer{
			Conf: &server.PeerConf{
				NeighborAddress: p.Address,
				PeerAs:          p.RemoteAS,
			},
			Transport: &server.Transport{
				PassiveMode: p.Passive,
			},
		}
		must(0, s.AddPeer(context.Background(), pp))
	}

	// Watch incoming BGP messages
	watcher := must(s.Watch(context.Background(), server.WatchBestPath(true), server.WatchPeer(true)))
	for ev := range watcher.Event() {
		switch msg := ev.(type) {
		case *server.WatchEventBestPath:
			for _, p := range msg.Paths {
				upd := BGPUpdate{
					Timestamp: time.Now().Unix(),
					Peer:      p.GetNeighbor().String(),
					MsgType:   "UPDATE",
				}
				// Extract prefixes
				if p.IsWithdraw() {
					upd.Withdraw = []string{p.GetNlri().String()}
				} else {
					upd.Announce = []string{p.GetNlri().String()}
				}
				// Minimal attrs (AS_PATH length, NEXT_HOP)
				attrs := map[string]any{}
				for _, a := range p.GetPathAttrs() {
					switch a := a.(type) {
					case *bgp.PathAttributeAsPath:
						attrs["as_path_len"] = a.Len()
					case *bgp.PathAttributeNextHop:
						attrs["next_hop"] = a.Value.String()
					}
				}
				upd.Attrs = attrs
				b := must(json.Marshal(upd))
				must(nc.Publish(cfg.NATS.Subject, b))
			}
		case *server.WatchEventPeer:
			// optional: publish peer up/down as synthetic events
		}
	}
}
