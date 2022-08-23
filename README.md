# dolesa
Simple web API for storing items into queue

## How To

### Build and Push Image to GCR
```shell
docker build . -t gcr.io/$PROJECT_NAME/dolesa
docker push gcr.io/$PROJECT_NAME/dolesa
```

### Deploy and Run in GCE

connect to the GCE instance
```shell
gcloud compute ssh --zone europe-west1-b $INSTANCE_NAME
```

then run the built Docker image
```shell
docker pull gcr.io/$PROJECT_NAME/dolesa
docker run --name dolesa-app --rm -d -p 80:8080 gcr.io/$PROJECT_NAME/dolesa
```

### Send a Message
```shell
curl -X POST http://$REMOTE_IP/send -u $USERNAME:$PASSWORD -d '{...}'
```
The user must have a `publisher` role.

### Receive a Message
```shell
curl -X POST http://$REMOTE_IP/receive -u $USERNAME:$PASSWORD
```
The user must have a `consumer` role.
