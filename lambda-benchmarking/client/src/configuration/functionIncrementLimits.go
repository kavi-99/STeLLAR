package configuration

import (
	log "github.com/sirupsen/logrus"
	"lambda-benchmarking/client/prompts"
	"math"
	"math/big"
	"time"
)

var cachedServiceTimeIncrement map[string]int64

func determineFunctionIncrementLimits(subExperiment *SubExperiment, standardIncrement int64, standardDurationMs int64) {
	for _, serviceTime := range subExperiment.DesiredServiceTimes {
		if cachedIncrement, ok := cachedServiceTimeIncrement[serviceTime]; ok {
			log.Infof("Using cached increment %d for desired %v", cachedIncrement, serviceTime)
			subExperiment.FunctionIncrementLimits = append(subExperiment.FunctionIncrementLimits, cachedIncrement)
			continue
		}

		parsedDesiredDuration, err := time.ParseDuration(serviceTime)
		if err != nil {
			log.Fatalf("Could not parse desired function run duration %s from configuration file.", serviceTime)
		}

		desiredDurationMs := parsedDesiredDuration.Milliseconds()
		log.Infof("Determining function increment for a duration of %dms...", desiredDurationMs)

		ratio := big.NewRat(desiredDurationMs, standardDurationMs)
		currentIncrement := big.NewRat(standardIncrement, 1)
		currentIncrement.Mul(currentIncrement, ratio)

		suggestedIncrementFloat, _ := currentIncrement.Float64()
		suggestedIncrement := int64(suggestedIncrementFloat)
		suggestedDurationMs := timeSession(suggestedIncrement).Milliseconds()
		if !almostEqual(suggestedDurationMs, desiredDurationMs, float64(desiredDurationMs)*0.02) {
			log.Warnf("Suggested increment %d (duration %dms) is not within 2%% of desired duration %dms",
				suggestedIncrement, suggestedDurationMs, desiredDurationMs)

			promptedIncrement := prompts.PromptForNumber("Please enter a better increment (leave empty for unchanged): ")
			if promptedIncrement != nil {
				suggestedIncrement = *promptedIncrement
			}
		}

		log.Infof("Using increment %d (timed ~%dms) for desired %dms", suggestedIncrement, suggestedDurationMs, desiredDurationMs)
		cachedServiceTimeIncrement[serviceTime] = suggestedIncrement
		subExperiment.FunctionIncrementLimits = append(subExperiment.FunctionIncrementLimits, suggestedIncrement)
	}
}

func timeSession(increment int64) time.Duration {
	start := time.Now()
	for i := int64(0); i < increment; i++ {
	}
	return time.Since(start)
}

func almostEqual(a, b int64, float64EqualityThreshold float64) bool {
	return math.Abs(float64(a-b)) <= float64EqualityThreshold
}