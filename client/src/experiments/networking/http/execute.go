// MIT License
//
// Copyright (c) 2020 Theodor Amariucai
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

package http

import (
	"context"
	log "github.com/sirupsen/logrus"
	"io/ioutil"
	"net/http"
	"net/http/httptrace"
	"time"
)

const (
	timeout = 15 * time.Minute
)

//ExecuteHTTPRequest will send an HTTP request, check its status code and return the response body.
func ExecuteHTTPRequest(req http.Request) ([]byte, time.Time, time.Time) {
	ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(timeout))
	defer cancel()

	resp, reqSentTime, reqReceivedTime := sendTimedRequest(ctx, req)

	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Errorf("Could not read HTTP response body: %s", err.Error())
	}

	if resp.StatusCode != http.StatusOK {
		log.Errorf("Response from %s had status %s: %s", req.URL.Hostname(), resp.Status, string(bodyBytes))
	}

	return bodyBytes, reqSentTime, reqReceivedTime
}

//https://stackoverflow.com/questions/48077098/getting-ttfb-time-to-first-byte-value-in-golang/48077762#48077762
func sendTimedRequest(ctx context.Context, req http.Request) (*http.Response, time.Time, time.Time) {
	var receivedFirstByte time.Time

	trace := &httptrace.ClientTrace{
		GotFirstResponseByte: func() {
			receivedFirstByte = time.Now()
		},
	}

	reqSentTime := time.Now()
	resp, err := http.DefaultTransport.RoundTrip(req.WithContext(httptrace.WithClientTrace(ctx, trace)))
	if err != nil {
		log.Fatalf("HTTP request failed with error %s", err.Error())
	}

	// For total time, return resp, reqSentTime, time.Now()
	return resp, reqSentTime, receivedFirstByte
}