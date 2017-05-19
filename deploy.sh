#!/bin/bash

docker build -t steemdata-mentions .
docker tag steemdata-mentions furion/steemdata-mentions
docker push furion/steemdata-mentions
