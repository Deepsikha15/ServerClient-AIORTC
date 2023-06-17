# Nimble Challenge

This project creates a server and client program that exchange data. The server generate continuous frames of a ball bouncing on the screen and sends the data to client. The client displays the frames and computes the coordinates and sends it back to the server. The server displays the received coordinates and computes the error with the current location of the ball.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## Installation

Run the following command to install project requirements.

```bash
pip3 install -r requirements.txt
```


## Usage

#### Execute from terminal
Run the following commands:

1. Open a terminal and run the server
    ```bash
   python3 server.py
    ```
2. Open a different terminal and run the client
    ```bash
   python3 client.py
    ```
   
#### Execute using docker images

Run the following commands:
1. Navigate to the folder Docker-Builds
2. Navigate to server directory
3. ```bash
   docker build -t server_docker .
    ```
4. Navigate to client directory
5. ```bash
   docker build -t client_docker .
    ```
6. The docker images can be directly loaded without the need for building. 
Go to the directory Docker-Images and run the following commands:
```bash
    docker load -i server_docker.tar
    socker load -i client_docker.tar
```
7. ```bash
   docker run -d --name server_container --network=host server_docker
   docker run -d --name client_container --network=host client_docker
   docker stop client_container
   docker stop server_container
   docker logs client_container
   docker logs server_container
    ```

#### Kubernetes Deployment
Install minikube

Traverse to the Kubernetes directory
```bash
    minikube start
    eval $(minikube docker-env)
    docker load -i ../Docker-Images/server_docker.tar
    docker load -i ../Docker-Images/client_docker.tar
    docker pull registry
    docker run -d -p 5000:5000 --name local-registry registry
    docker tag server_docker localhost:5000/server_docker:latest
    docker tag client_docker localhost:5000/client_docker:latest
    docker push localhost:5000/server_docker:latest
    docker push localhost:5000/client_docker:latest
    kubectl apply -f server_deployment.yaml
    kubectl apply -f client_deployment.yaml
```

Describe the expected output or any additional setup required.

1. You can visualize the displayed frames from the client.
2. The server terminal will show the received coordinates and associated error. The error is calculated as the distance between the received coordinates and the current location of the ball.
3. Let the server and client run for sometime after which you can stop the client at your will (Ctrl + C).
    Since it is a continuous data exchange the server and client will run indefinitely. When any one of them is stopped, the other stops automatically.


### Unit Testing

From the main working directory
```commandline
pytest test_pytest.py
```

## Features

The project has the following flavors:

1. Server sends an offer to the client
2. Client receives the offer and sends an answer to the server
3. Server generates continuous 2D images of a bouncing ball
4. Server sends these images to the client using frame transport
5. Client displays the images
6. Client starts a new process to compute the coordinates of the ball in the received images
7. A function to parse the image to get the coordinates called by the new process
8. The main client thread sends the coordinates to the server across a datachannel
9. The server displays the received coordinates and the computed error
10. Unit tests for server, client and utility functions
11. A video of the running application
12. Docker images for server and client
13. Kubernetes manifest files to deploy server and client

## Contact

- Email: deepsikha96.das@gmail.com
