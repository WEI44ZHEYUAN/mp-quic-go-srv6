module qerr

go 1.21.9

replace h2quic => ../h2quic

replace internal => ../internal

replace ackhandler => ../ackhandler

replace congestion => ../congestion

replace mp-quic => ../../mp-quic

replace bifurcation => ../bifurcation

require (
	github.com/onsi/ginkgo v1.16.5
	github.com/onsi/gomega v1.32.0
	internal v0.0.0-00010101000000-000000000000
)

require (
	github.com/fsnotify/fsnotify v1.4.9 // indirect
	github.com/google/go-cmp v0.6.0 // indirect
	github.com/nxadm/tail v1.4.8 // indirect
	golang.org/x/net v0.23.0 // indirect
	golang.org/x/sys v0.18.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	gopkg.in/tomb.v1 v1.0.0-20141024135613-dd632973f1e7 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
