build-docker:
	docker build -t sandybot .

bash:
	docker run --rm -it \
        --env-file .env \
	    -v $$(pwd)/:/shared --workdir /shared \
	    sandybot bash

run:
	export $$(cat .env | xargs) && \
	./venv/bin/python3 main.py

run-timepatched:
	export LD_PRELOAD=./libfaketime.so.1 && \
	export FAKETIME_DONT_FAKE_MONOTONIC=1 && \
	export FAKETIME="$(shell curl -s http://worldclockapi.com/api/json/est/now | jq -r '.currentDateTime' | tr 'T' ' ' | cut -b -16):00" && \
	$(MAKE) run

