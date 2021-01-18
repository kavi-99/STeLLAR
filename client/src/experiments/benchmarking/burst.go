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

package benchmarking

import (
	log "github.com/sirupsen/logrus"
	"net/http"
	"sync"
	vHiveBenchHTTP "vhive-bench/client/experiments/networking/http"
	"vhive-bench/client/setup"
)

func sendBurst(provider string, config setup.SubExperiment, burstID int, requests int, gatewayEndpointID string,
	assignedFunctionIncrementLimit int64, safeExperimentWriter *SafeWriter) {
	request := vHiveBenchHTTP.CreateRequest(provider, config.PayloadLengthBytes, gatewayEndpointID, assignedFunctionIncrementLimit)

	log.Infof("[sub-experiment %d] Starting burst %d, making %d requests with increment limit %d to (%s).",
		config.ID,
		burstID,
		requests,
		assignedFunctionIncrementLimit,
		request.URL.Hostname(),
	)

	var requestsWaitGroup sync.WaitGroup
	for i := 0; i < requests; i++ {
		requestsWaitGroup.Add(1)
		go generateLatencyRecord(&requestsWaitGroup, provider, *request, safeExperimentWriter, burstID)
	}
	requestsWaitGroup.Wait()
	log.Infof("[sub-experiment %d] Received all responses for burst %d.", config.ID, burstID)
}

func generateLatencyRecord(requestsWaitGroup *sync.WaitGroup, provider string, request http.Request,
	safeExperimentWriter *SafeWriter, burstID int) {
	defer requestsWaitGroup.Done()

	respBody, reqSentTime, reqReceivedTime := vHiveBenchHTTP.ExecuteHTTPRequest(request)

	var responseID string
	switch provider {
	case "aws":
		responseID = vHiveBenchHTTP.GetAWSRequestID(respBody)
	default:
		responseID = ""
	}

	safeExperimentWriter.recordLatencyRecord(request.URL.Hostname(), reqSentTime, reqReceivedTime, responseID, burstID)
}