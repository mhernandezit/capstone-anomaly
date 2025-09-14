package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"time"

	"github.com/nats-io/nats.go"
	"github.com/sirupsen/logrus"
)

// BMP Message Types (RFC 7854)
const (
	BMPTypeRouteMonitoring       = 0
	BMPTypeStatisticsReport      = 1
	BMPTypePeerDownNotification  = 2
	BMPTypePeerUpNotification    = 3
	BMPTypeInitiationMessage     = 4
	BMPTypeTerminationMessage    = 5
	BMPTypeRouteMirroringMessage = 6
)

// BMP Header structure
type BMPHeader struct {
	Version  uint8
	Length   uint32
	Type     uint8
	Reserved uint8
}

// BMP Peer Header
type BMPPeerHeader struct {
	Type            uint8
	Flags           uint8
	Distinguisher   uint64
	Address         net.IP
	AS              uint32
	BGPID           uint32
	Timestamp       time.Time
	TimestampMicros uint32
}

// BGP Update Message
type BGPUpdate struct {
	Timestamp string   `json:"timestamp"`
	Peer      string   `json:"peer"`
	Type      string   `json:"type"`
	Announce  []string `json:"announce,omitempty"`
	Withdraw  []string `json:"withdraw,omitempty"`
	ASPath    string   `json:"as_path,omitempty"`
	NextHop   string   `json:"next_hop,omitempty"`
	Origin    string   `json:"origin,omitempty"`
	LocalPref uint32   `json:"local_pref,omitempty"`
	MED       uint32   `json:"med,omitempty"`
}

// BMP Collector
type BMPCollector struct {
	conn     net.Conn
	natsConn *nats.Conn
	logger   *logrus.Logger
	peers    map[string]*BMPPeerHeader
}

func NewBMPCollector(natsURL string) (*BMPCollector, error) {
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	// Connect to NATS
	nc, err := nats.Connect(natsURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}

	return &BMPCollector{
		natsConn: nc,
		logger:   logger,
		peers:    make(map[string]*BMPPeerHeader),
	}, nil
}

func (c *BMPCollector) Connect(addr string) error {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to connect to BMP server: %w", err)
	}
	c.conn = conn
	c.logger.Infof("Connected to BMP server at %s", addr)
	return nil
}

func (c *BMPCollector) Close() error {
	if c.conn != nil {
		c.conn.Close()
	}
	if c.natsConn != nil {
		c.natsConn.Close()
	}
	return nil
}

func (c *BMPCollector) readBMPHeader() (*BMPHeader, error) {
	header := &BMPHeader{}

	// Read BMP header (8 bytes)
	buf := make([]byte, 8)
	_, err := io.ReadFull(c.conn, buf)
	if err != nil {
		return nil, err
	}

	header.Version = buf[0]
	header.Length = binary.BigEndian.Uint32(buf[1:5])
	header.Type = buf[5]
	header.Reserved = buf[6]

	return header, nil
}

func (c *BMPCollector) readPeerHeader() (*BMPPeerHeader, error) {
	peer := &BMPPeerHeader{}

	// Read peer header (42 bytes)
	buf := make([]byte, 42)
	_, err := io.ReadFull(c.conn, buf)
	if err != nil {
		return nil, err
	}

	peer.Type = buf[0]
	peer.Flags = buf[1]
	peer.Distinguisher = binary.BigEndian.Uint64(buf[2:10])

	// IP address (16 bytes for IPv6, but we'll handle both)
	if peer.Flags&0x80 != 0 { // IPv6
		peer.Address = net.IP(buf[10:26])
	} else { // IPv4
		peer.Address = net.IP(buf[26:30])
	}

	peer.AS = binary.BigEndian.Uint32(buf[30:34])
	peer.BGPID = binary.BigEndian.Uint32(buf[34:38])

	// Timestamp
	timestamp := binary.BigEndian.Uint32(buf[38:42])
	peer.Timestamp = time.Unix(int64(timestamp), 0)

	return peer, nil
}

func (c *BMPCollector) processBGPMessage(peer *BMPPeerHeader, bgpData []byte) error {
	// This is a simplified BGP message parser
	// In a full implementation, you'd parse the complete BGP message structure

	if len(bgpData) < 19 { // Minimum BGP message size
		return fmt.Errorf("BGP message too short")
	}

	// BGP message type
	msgType := bgpData[18]

	peerKey := peer.Address.String()
	c.peers[peerKey] = peer

	update := &BGPUpdate{
		Timestamp: time.Now().Format(time.RFC3339),
		Peer:      peer.Address.String(),
		ASPath:    fmt.Sprintf("%d", peer.AS),
		NextHop:   peer.Address.String(),
	}

	switch msgType {
	case 2: // UPDATE message
		update.Type = "UPDATE"
		// Parse UPDATE message (simplified)
		// In reality, you'd parse NLRI, withdrawn routes, path attributes, etc.
		update.Announce = []string{"0.0.0.0/0"} // Placeholder

	case 3: // NOTIFICATION message
		update.Type = "NOTIFICATION"

	case 4: // KEEPALIVE message
		update.Type = "KEEPALIVE"

	default:
		update.Type = "UNKNOWN"
	}

	// Publish to NATS
	updateJSON, err := json.Marshal(update)
	if err != nil {
		return fmt.Errorf("failed to marshal update: %w", err)
	}

	err = c.natsConn.Publish("bgp.updates", updateJSON)
	if err != nil {
		return fmt.Errorf("failed to publish to NATS: %w", err)
	}

	c.logger.Debugf("Published BGP update: %s from peer %s", update.Type, peer.Address.String())
	return nil
}

func (c *BMPCollector) processBMPMessage() error {
	header, err := c.readBMPHeader()
	if err != nil {
		return fmt.Errorf("failed to read BMP header: %w", err)
	}

	c.logger.Debugf("Received BMP message: type=%d, length=%d", header.Type, header.Length)

	// Read the rest of the message
	messageData := make([]byte, header.Length-8)
	_, err = io.ReadFull(c.conn, messageData)
	if err != nil {
		return fmt.Errorf("failed to read BMP message data: %w", err)
	}

	switch header.Type {
	case BMPTypeRouteMonitoring:
		// Parse peer header
		peer, err := c.readPeerHeader()
		if err != nil {
			return fmt.Errorf("failed to read peer header: %w", err)
		}

		// Process BGP message
		bgpData := messageData[42:] // Skip peer header
		err = c.processBGPMessage(peer, bgpData)
		if err != nil {
			c.logger.Errorf("Failed to process BGP message: %v", err)
		}

	case BMPTypePeerUpNotification:
		peer, err := c.readPeerHeader()
		if err != nil {
			return fmt.Errorf("failed to read peer header: %w", err)
		}
		c.logger.Infof("Peer up: %s (AS%d)", peer.Address.String(), peer.AS)

	case BMPTypePeerDownNotification:
		peer, err := c.readPeerHeader()
		if err != nil {
			return fmt.Errorf("failed to read peer header: %w", err)
		}
		c.logger.Infof("Peer down: %s (AS%d)", peer.Address.String(), peer.AS)

	case BMPTypeInitiationMessage:
		c.logger.Info("BMP initiation message received")

	case BMPTypeTerminationMessage:
		c.logger.Info("BMP termination message received")

	default:
		c.logger.Debugf("Unhandled BMP message type: %d", header.Type)
	}

	return nil
}

func (c *BMPCollector) Run() error {
	c.logger.Info("Starting BMP collector...")

	for {
		err := c.processBMPMessage()
		if err != nil {
			if err == io.EOF {
				c.logger.Info("BMP connection closed by server")
				break
			}
			c.logger.Errorf("Error processing BMP message: %v", err)
			// Continue processing other messages
		}
	}

	return nil
}

func main() {
	// Configuration
	bmpServer := "localhost:1790" // Default BMP port
	natsURL := "nats://localhost:4222"

	// Create collector
	collector, err := NewBMPCollector(natsURL)
	if err != nil {
		logrus.Fatalf("Failed to create BMP collector: %v", err)
	}
	defer collector.Close()

	// Connect to BMP server
	err = collector.Connect(bmpServer)
	if err != nil {
		logrus.Fatalf("Failed to connect to BMP server: %v", err)
	}

	// Run collector
	err = collector.Run()
	if err != nil {
		logrus.Fatalf("BMP collector error: %v", err)
	}
}
