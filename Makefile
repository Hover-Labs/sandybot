build-docker:
	docker build -t sandybot .

bash:
	docker run --rm -it \
        --env-file .env \
	    -v $$(pwd)/:/shared --workdir /shared \
	    sandybot bash

run:
	export $$(cat .env | xargs) && ./venv/bin/python3 main.py
