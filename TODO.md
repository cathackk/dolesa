# TODO

## features
- [ ] JSON schema validation
- [ ] user permissions per queue
- [ ] reset queue (`POST /queues/{q}/reset`?)
- [x] multiple queues:
  - [x] queue list
  - [x] endpoints (`POST /queues/{q}/send`, `POST /queues/{q}/receive`)
  - [x] list available queues (`GET /queues`)
  - [x] default queue
- [x] warning if using default users config


## QA
- [ ] unit testing
- [x] linters
- [ ] black


## CI
- [ ] CI (github actions)


## security
- [ ] proper secrets
- [ ] https


## product
- [ ] use pika channels for routing
- [ ] rabbitmq image without management
- [ ] Swagger
- [ ] update README.md
