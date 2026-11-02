package main

import (
	"strings"
	"testing"
)

func TestFormatMessageMarketPriceEnvelope(t *testing.T) {
	frame := []byte(`{"meta":{"type":"market_price"},"data":{"event_id":"event-123","affiliate_id":22,"market_id":3,"normalized_market_participant_id":456,"line":2.5,"price":-115,"previous_price":-110}}`)
	got, ok, err := formatMessage(frame)
	if err != nil {
		t.Fatal(err)
	}
	if !ok {
		t.Fatal("market_price message was ignored")
	}
	for _, part := range []string{"event-123", "book 22", "market 3", "participant 456", "line 2.5", "-110 -> -115"} {
		if !strings.Contains(got, part) {
			t.Errorf("formatted output %q missing %q", got, part)
		}
	}
}

func TestFormatMessageIgnoresHeartbeat(t *testing.T) {
	got, ok, err := formatMessage([]byte(`{"meta":{"type":"heartbeat"},"data":{}}`))
	if err != nil {
		t.Fatal(err)
	}
	if ok || got != "" {
		t.Fatalf("heartbeat produced output %q, ok=%v", got, ok)
	}
}

func TestFormatMessageAllowsMissingPreviousPrice(t *testing.T) {
	got, ok, err := formatMessage([]byte(`{"meta":{"type":"market_price"},"data":{"event_id":"event-123","price":"-117"}}`))
	if err != nil || !ok || !strings.Contains(got, "? -> -117") {
		t.Fatalf("missing previous price was not handled: %q, %v", got, err)
	}
}
