export PYTHONPATH="/app/"
cd /app/muggle/package
modprobe fuse
python3.9 runner.py
cd /tmp/muggle_dist && ls && tar -cvzf main.dist.tar.gz main.dist/
ls
