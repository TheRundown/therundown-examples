// Fetch today's NBA events and print open main moneyline prices.
//
// Requires the RUNDOWN_KEY env var. Run: go run fetch_events.go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const base = "https://therundown.io/api/v2"

var allowedBooks = map[string]bool{"19": true, "22": true, "23": true}

type quote struct {
	Price     json.RawMessage `json:"price"`
	ClosedAt  string          `json:"closed_at"`
	UpdatedAt string          `json:"updated_at"`
}

type line struct {
	Prices map[string]quote `json:"prices"`
}
type participant struct {
	ID    int    `json:"id"`
	Type  string `json:"type"`
	Name  string `json:"name"`
	Lines []line `json:"lines"`
}
type market struct {
	MarketID     int           `json:"market_id"`
	PeriodID     int           `json:"period_id"`
	Participants []participant `json:"participants"`
}
type event struct {
	EventID   string `json:"event_id"`
	EventDate string `json:"event_date"`
	Teams     []struct {
		Name   string `json:"name"`
		IsHome bool   `json:"is_home"`
	} `json:"teams"`
	Markets []market `json:"markets"`
}
type response struct {
	Events []event `json:"events"`
}

func run(client *http.Client, output io.Writer, key, today string) error {
	u, err := url.Parse(fmt.Sprintf("%s/sports/4/events/%s", base, today))
	if err != nil {
		return fmt.Errorf("build request URL: %w", err)
	}
	q := u.Query()
	q.Set("affiliate_ids", "19,22,23")
	q.Set("market_ids", "1")
	q.Set("main_line", "true")
	q.Set("hide_closed", "true")
	u.RawQuery = q.Encode()
	req, err := http.NewRequest(http.MethodGet, u.String(), nil)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("X-TheRundown-Key", key)
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("fetch events: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("events request returned HTTP %d", resp.StatusCode)
	}
	var data response
	dec := json.NewDecoder(resp.Body)
	dec.UseNumber()
	if err := dec.Decode(&data); err != nil {
		return fmt.Errorf("decode events response: %w", err)
	}
	if len(data.Events) == 0 {
		_, err := fmt.Fprintf(output, "No NBA events on %s.\n", today)
		return err
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
		if _, err := fmt.Fprintf(output, "\n%s @ %s  (%s)\n", away, home, ev.EventDate); err != nil {
			return err
		}
		for _, m := range ev.Markets {
			if m.MarketID != 1 && m.MarketID != 41 {
				continue
			}
			for _, p := range m.Participants {
				for _, l := range p.Lines {
					for bookID, price := range l.Prices {
						if !allowedBooks[bookID] || price.ClosedAt != "" {
							continue
						}
						rawPrice := strings.TrimSpace(string(price.Price))
						if strings.HasPrefix(rawPrice, "\"") {
							var numeric string
							if json.Unmarshal(price.Price, &numeric) != nil {
								continue
							}
							rawPrice = numeric
						}
						value, err := json.Number(rawPrice).Float64()
						if err != nil || math.IsNaN(value) || math.IsInf(value, 0) || value == 0 || value == 0.0001 {
							continue
						}
						if _, err := fmt.Fprintf(output, "  market %d period %d participant %s (id=%d, type=%s) book %s: %g\n",
							m.MarketID, m.PeriodID, p.Name, p.ID, p.Type, bookID, value); err != nil {
							return err
						}
					}
				}
			}
		}
	}
	return nil
}

func main() {
	key := os.Getenv("RUNDOWN_KEY")
	if key == "" {
		log.Fatal("RUNDOWN_KEY env var is required")
	}
	client := &http.Client{Timeout: 15 * time.Second}
	if err := run(client, os.Stdout, key, time.Now().UTC().Format("2006-01-02")); err != nil {
		log.Fatal(err)
	}
}
