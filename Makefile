test:
	pkill node &
	pkill "server-app" -f &
	http-server -p 8000 &
	python server-app/main.py &

stop_test:
	pkill node
	pkill "server-app" -f &