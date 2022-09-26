# SCVL Full Truck Load

This project demonstrates the use of semantically annotated data posted to a distributed ledger for the case of Full Truck Load cargo transport.

## Installation

### Building

```shell script
docker-compose build
```

### Configuration

```shell script
docker-compose run ftl_app sh setup.sh
```

### Running

```shell script
docker-compose up -d
```

### Testing

```shell script
docker-compose exec ftl_app python manage.py test api.tests
```

## Documentation

### API wiki

[Wiki endpoint specification](https://ci.tno.nl/gitlab/scvl/scvl-ftl/wikis/api-calls/endpoints)

### OpenAPI Docs

1. Log in as root/hallo123 at http://bctb2.sensorlab.tno.nl:84/admin to gain admin rights on the FTL app.

2. Read the functional documentation of the endpoints at http://bctb2.sensorlab.tno.nl:84/api/docs

3. Try out requests using e.g. curl or Postman, specifying `Authorization = Token your-token-here` in the header. (Get the token for root/hallo123 at http://bctb2.sensorlab.tno.nl:84/api/auth_token/root/hallo123 )
