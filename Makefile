CONTAINER_NAME = skill-router
IMAGE_NAME = skill-router
PORT ?= 8006

build:
	docker build -t $(IMAGE_NAME) .

start:
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):8000 $(IMAGE_NAME)

stop:
	docker stop -t 0 $(CONTAINER_NAME) || true && docker rm -f $(CONTAINER_NAME)

restart: stop start
