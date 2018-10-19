CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o ./skyfire/skyfire ./skyfire/skyfire.go

docker build -t docker.io/mikephammer/skyfire ./skyfire/.

docker push docker.io/mikephammer/skyfire 
