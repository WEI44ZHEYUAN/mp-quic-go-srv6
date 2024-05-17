module benchmark

go 1.21.9

replace h2quic => ../h2quic

replace internal => ../internal

replace qerr => ../qerr

replace ackhandler => ../ackhandler

replace congestion => ../congestion

replace mp-quic => ../../mp-quic

replace integrationtests => ../integrationtests

replace bifurcation => ../bifurcation

require (
	github.com/onsi/ginkgo v1.16.5
	github.com/onsi/gomega v1.32.0
	internal v0.0.0-00010101000000-000000000000
	mp-quic v0.0.0-00010101000000-000000000000
)

require bifurcation v0.0.0-00010101000000-000000000000 // indirect

require (
	ackhandler v0.0.0-00010101000000-000000000000 // indirect
	congestion v0.0.0-00010101000000-000000000000 // indirect
	github.com/bifurcation/mint v0.0.0-20210616192047-fd18df995463 // indirect
	github.com/fsnotify/fsnotify v1.4.9 // indirect
	github.com/google/go-cmp v0.6.0 // indirect
	github.com/hashicorp/golang-lru v1.0.2 // indirect
	github.com/lucas-clemente/aes12 v0.0.0-20171027163421-cd47fb39b79f // indirect
	github.com/lucas-clemente/fnv128a v0.0.0-20160504152609-393af48d3916 // indirect
	github.com/lucas-clemente/quic-go-certificates v0.0.0-20160823095156-d2f86524cced // indirect
	github.com/nxadm/tail v1.4.8 // indirect
	golang.org/x/crypto v0.21.0 // indirect
	golang.org/x/net v0.23.0 // indirect
	golang.org/x/sys v0.18.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	gopkg.in/tomb.v1 v1.0.0-20141024135613-dd632973f1e7 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
	integrationtests v0.0.0-00010101000000-000000000000
	qerr v0.0.0-00010101000000-000000000000 // indirect
)
