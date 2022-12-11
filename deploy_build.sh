#docker kill $(docker ps -a -q)
#docker rm $(docker ps -a -q)
#docker rmi $(docker images -q -f dangling=true)

docker container prune
docker image prune
docker volume prune
docker builder prune
docker system prune --volumes -a
docker rm deploy_compile && docker rmi deploy_compile
docker build -t deploy_compile -f Dockerfile_Compile .
docker container run -it --device /dev/fuse --cap-add SYS_ADMIN --privileged --name=deploy_compile -d deploy_compile
docker exec -it deploy_compile /bin/bash -c "rm -rf /usr/local/lib/python3.9/site-packages/gevent/tests"
docker exec -it deploy_compile /bin/bash -c '/app/muggle/package/lib/compile.sh'
if [ ! -d output  ]; then mkdir output; fi && docker cp deploy_compile:/tmp/muggle_dist/main.dist.tar.gz ./output
docker cp deploy_compile:/tmp/muggle_dist/main.bin ./output
docker cp deploy_compile:/tmp/muggle_dist/ext.so ./output
docker cp deploy_compile:/tmp/muggle_dist/engine.map ./output