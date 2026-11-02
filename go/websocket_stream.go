// Log market price-change messages from the TheRundown WebSocket.
// Ultra tier and above. This example logs individual updates; it does not
// maintain a market snapshot or infer closes.
//
// Requires RUNDOWN_KEY and github.com/gorilla/websocket.
// Run: go run websocket_stream.go
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/url"
	"os"

	"github.com/gorilla/websocket"
)

type envelope struct {
	Meta struct {
		Type string `json:"type"`
	} `json:"meta"`
	Data struct {
		EventID       string `json:"event_id"`
		AffiliateID   int    `json:"affiliate_id"`
		MarketID      int    `json:"market_id"`
		ParticipantID int    `json:"normalized_market_participant_id"`
		Line          any    `json:"line"`
		Price         any    `json:"price"`
		PreviousPrice any    `json:"previous_price"`
	} `json:"data"`
}

func formatMessage(raw []byte) (string, bool, error) {
	var msg envelope
	if err := json.Unmarshal(raw, &msg); err != nil {
		return "", false, fmt.Errorf("parse message: %w", err)
	}
	if msg.Meta.Type != "market_price" {
		return "", false, nil
	}
	if msg.Data.EventID == "" {
		return "", false, errors.New("market_price message missing data.event_id")
	}
	previous := msg.Data.PreviousPrice
	if previous == nil {
		previous = "?"
	}
	return fmt.Sprintf("event %s book %d market %d participant %d line %v %v -> %v",
		msg.Data.EventID, msg.Data.AffiliateID, msg.Data.MarketID,
		msg.Data.ParticipantID, msg.Data.Line, previous, msg.Data.Price), true, nil
}

func main() {
	key := os.Getenv("RUNDOWN_KEY")
	if key == "" {
		log.Fatal("RUNDOWN_KEY env var is required")
	}
	u := url.URL{Scheme: "wss", Host: "therundown.io", Path: "/api/v2/ws/markets"}
	q := u.Query()
	q.Set("sport_ids", "4")
	q.Set("affiliate_ids", "19,22,23")
	q.Set("market_ids", "1,2,3")
	q.Set("main_line", "true")
	u.RawQuery = q.Encode()
	conn, _, err := websocket.DefaultDialer.Dial(u.String(), map[string][]string{"X-TheRundown-Key": {key}})
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	fmt.Println("connected, logging market price changes...")
	for {
		_, raw, err := conn.ReadMessage()
		if err != nil {
			log.Println("read:", err)
			return
		}
		line, ok, err := formatMessage(raw)
		if err != nil {
			log.Println(err)
			continue
		}
		if ok {
			fmt.Println(line)
		}
	}
}
