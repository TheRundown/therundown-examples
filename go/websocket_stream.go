// Stream every line move in real time via the TheRundown WebSocket.
// Pro tier and above.
//
// Requires:
//   - RUNDOWN_KEY env var
//   - go get github.com/gorilla/websocket
//
// Run:  go run websocket_stream.go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/url"
	"os"

	"github.com/gorilla/websocket"
)

func main() {
	key := os.Getenv("RUNDOWN_KEY")
	if key == "" {
		log.Fatal("RUNDOWN_KEY env var is required")
	}

	u := url.URL{
		Scheme:   "wss",
		Host:     "therundown.io",
		Path:     "/api/v2/ws/markets",
		RawQuery: "key=" + url.QueryEscape(key),
	}

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	fmt.Println("connected, streaming line moves...")

	for {
		_, raw, err := conn.ReadMessage()
		if err != nil {
			log.Println("read:", err)
			return
		}
		var msg map[string]any
		if err := json.Unmarshal(raw, &msg); err != nil {
			log.Println("parse:", err)
			continue
		}
		fmt.Printf("event %v  book %v  market %v  -> %v\n",
			msg["event_id"], msg["affiliate_id"],
			msg["market_id"], msg["prices"])
	}
}
