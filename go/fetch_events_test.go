package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"strings"
	"testing"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (fn roundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) { return fn(req) }

func fixturePayload(t *testing.T) []byte {
	t.Helper()
	body, err := os.ReadFile("../tests/fixtures/v2-event.json")
	if err != nil {
		t.Fatal(err)
	}
	return body
}

func TestRunDecodesNestedFixtureAndBuildsBoundedAuthenticatedRequest(t *testing.T) {
	const date = "2026-11-01"
	client := &http.Client{Transport: roundTripFunc(func(req *http.Request) (*http.Response, error) {
		if req.Method != http.MethodGet || req.URL.Path != "/api/v2/sports/4/events/"+date {
			t.Errorf("unexpected request: %s %s", req.Method, req.URL)
		}
		if req.Header.Get("X-TheRundown-Key") != "dummy-test-key" {
			t.Errorf("missing auth header")
		}
		if _, ok := req.URL.Query()["key"]; ok {
			t.Errorf("API key leaked into query")
		}
		q := req.URL.Query()
		if q.Get("affiliate_ids") != "19,22,23" || q.Get("market_ids") != "1" || q.Get("main_line") != "true" || q.Get("hide_closed") != "true" {
			t.Errorf("unexpected request filters: %v", q)
		}
		return &http.Response{StatusCode: 200, Body: io.NopCloser(bytes.NewReader(fixturePayload(t))), Header: make(http.Header)}, nil
	})}
	var output bytes.Buffer
	if err := run(client, &output, "dummy-test-key", date); err != nil {
		t.Fatal(err)
	}
	got := output.String()
	for _, want := range []string{"Buffalo Bills", "Baltimore Ravens", "market 1 period 0", "book 19", "book 23", "-170", "142"} {
		if !strings.Contains(got, want) {
			t.Errorf("output missing %q:\n%s", want, got)
		}
	}
	if strings.Count(got, "book ") != 4 {
		t.Errorf("expected four open quotes, got:\n%s", got)
	}
}

func TestRunSkipsClosedOffboardSentinelAndInvalidPricesButKeepsReopenedQuote(t *testing.T) {
	var data response
	dec := json.NewDecoder(bytes.NewReader(fixturePayload(t)))
	dec.UseNumber()
	if err := dec.Decode(&data); err != nil {
		t.Fatal(err)
	}
	first := &data.Events[0].Markets[0].Participants[0].Lines[0].Prices
	(*first)["19"] = quote{Price: json.RawMessage("-170"), ClosedAt: "2026-10-30T00:00:00Z"}
	(*first)["22"] = quote{Price: json.RawMessage(`"-160"`), ClosedAt: "", UpdatedAt: "2000-01-01T00:00:00Z"} // Empty closed_at means open, regardless of old update time.
	(*first)["24"] = quote{Price: json.RawMessage("-155")}                                                    // Not in the requested book allowlist.
	second := &data.Events[0].Markets[0].Participants[1].Lines[0].Prices
	(*second)["22"] = quote{Price: json.RawMessage("0.0001000")}
	(*second)["19"] = quote{Price: json.RawMessage(`"NaN"`)}
	payload, err := json.Marshal(data)
	if err != nil {
		t.Fatal(err)
	}
	client := &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 200, Body: io.NopCloser(bytes.NewReader(payload)), Header: make(http.Header)}, nil
	})}
	var output bytes.Buffer
	if err := run(client, &output, "dummy", "2026-11-01"); err != nil {
		t.Fatal(err)
	}
	got := output.String()
	if strings.Contains(got, "book 24") || strings.Contains(got, "NaN") || strings.Contains(got, "0.0001000") || strings.Contains(got, "-170") {
		t.Errorf("closed/offboard/sentinel/invalid quote was printed:\n%s", got)
	}
	if !strings.Contains(got, "book 22: -160") {
		t.Errorf("empty closed_at quote was not treated as open:\n%s", got)
	}
}

func TestRunReturnsHTTPStatusWithoutResponseBody(t *testing.T) {
	client := &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 503, Body: io.NopCloser(strings.NewReader("private upstream details")), Header: make(http.Header)}, nil
	})}
	err := run(client, io.Discard, "dummy", "2026-11-01")
	if err == nil || !strings.Contains(err.Error(), "HTTP 503") {
		t.Fatalf("expected HTTP status error, got %v", err)
	}
	if strings.Contains(err.Error(), "private upstream details") {
		t.Fatal("response body leaked in error")
	}
}
