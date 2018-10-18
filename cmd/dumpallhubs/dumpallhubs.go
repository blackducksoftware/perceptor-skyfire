package main

import (
	"encoding/json"
	"fmt"
	"os"

	hub "github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/viper"
)

type HubConfig struct {
	Hub_URLs []string
	Username string
	Password string
}

func main() {
	fmt.Println("Get Path to config file", os.Args[1])
	configPath := os.Args[1]

	log.Infof("Read in the config file")
	config, err := GetConfig(configPath)
	if err != nil {
		panic(err)
	}

	username := config.Username
	password := config.Password

	fmt.Println("Iterate through URLs", len(config.Hub_URLs))
	for _, url := range config.Hub_URLs {
		fmt.Println("Found a URL")
		hubDumper, err := hub.NewHubDumper(url, username, password)
		if err != nil {
			panic(err)
		}

		hubDump, err := hubDumper.Dump()
		if err != nil {
			panic(err)
		}
		//hubReport := report.NewHubReport(hubDump)

		dict := map[string]interface{}{
			"Dump": hubDump,
			//"Report": hubReport,
		}

		bytes, err := json.MarshalIndent(dict, "", "  ")
		if err != nil {
			panic(err)
		}

		fmt.Println(string(bytes))
	}

}

// GetConfig returns a configuration object to configure Perceptor
func GetConfig(configPath string) (*HubConfig, error) {
	var config *HubConfig

	viper.SetConfigFile(configPath)

	err := viper.ReadInConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %v", err)
	}

	err = viper.Unmarshal(&config)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %v", err)
	}

	return config, nil
}
