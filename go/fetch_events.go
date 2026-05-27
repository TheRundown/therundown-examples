// Fetch today's NBA events and print the moneyline for each game.
//
// Requires the RUNDOWN_KEY env var. Get one at
// https://therundown.io/docs/quickstart.
//
// Run:  go run fetch_events.go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"time"
)

const base = "https://therundown.io/api/v2"

// Sport IDs come from /api/v2/sports. NBA is 4.
const nbaSportID = 4

// Affiliate IDs come from /api/v2/affiliates.
const affiliates = "3,19,23"

type team struct {
	Name   string `json:"name"`
	IsHome bool   `json:"is_home"`
}

type moneyline struct {
	Home int `json:"home"`
	Away int `json:"away"`
}

type markets struct {
	Moneyline *moneyline `json:"moneyline,omitempty"`
}

type event struct {
	EventID   string             `json:"event_id"`
	EventDate string             `json:"event_date"`
	Teams     []team             `json:"teams"`
	Lines     map[string]markets `json:"lines"`
}

type response struct {
	Events []event `json:"events"`
}

func main() {
	key := os.Getenv("RUNDOWN_KEY")
	if key == "" {
		log.Fatal("RUNDOWN_KEY env var is required")
	}

	today := time.Now().Format("2006-01-02")
	u, _ := url.Parse(fmt.Sprintf("%s/sports/%d/events/%s", base, nbaSportID, today))
	q := u.Query()
	q.Set("key", key)
	q.Set("affiliate_ids", affiliates)
	q.Set("market_ids", "1,2,3")
	q.Set("main_line", "true")
	u.RawQuery = q.Encode()

	resp, err := http.Get(u.String())
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		log.Fatalf("HTTP %d: %s", resp.StatusCode, body)
	}

	var data response
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		log.Fatal(err)
	}

	if len(data.Events) == 0 {
		fmt.Printf("No NBA events on %s.\n", today)
		return
	}

	for _, ev := range data.Events {
		var home, away string
		for _, t := range ev.Teams {
			if t.IsHome {
				home = t.Name
			} else {
				away = t.Name
			}
		}
		fmt.Printf("\n%s @ %s  (%s)\n", away, home, ev.EventDate)

		for affID, m := range ev.Lines {
			if m.Moneyline != nil {
				fmt.Printf("  book %s: home=%d  away=%d\n",
					affID, m.Moneyline.Home, m.Moneyline.Away)
			}
		}
	}
}
