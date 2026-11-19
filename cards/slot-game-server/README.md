# Slot-Game-Server



### Build slot-build-env and slot-prod-env image

```bash
docker build --no-cache -t gitlab-registry.iplaystar.net:5005/game-server/slot-game-server/slot-build-env:1.0.0 .
docker build --no-cache -t gitlab-registry.iplaystar.net:5005/game-server/slot-game-server/slot-prod-env:1.0.0 .
```



### Build slot-game-server image

```bash
docker build --no-cache \
             --build-arg DEV_MODE=ON \
             --build-arg SCRIPT_MODE=ON \
             -t gitlab-registry.iplaystar.net:5005/game-server/slot-game-server/slot-game-server:dev-test .
```

### docker run
```bash
docker run --name slot-gs \
           --privileged \
           -p 1107:1107 \
           -v $(pwd)/game-server.properties:/app/game-server.properties \
           -d gitlab-registry.iplaystar.net:5005/game-server/slot-game-server/slot-game-server:dev-test
```



