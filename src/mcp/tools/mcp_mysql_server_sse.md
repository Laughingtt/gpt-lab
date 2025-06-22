docker run -d \
  --name mysql-mcp-server-sse \
  -e HOST=0.0.0.0 \
  -e PORT=3000 \
  -e MYSQL_HOST=127.0.0.1 \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=custom_user \
  -e MYSQL_PASSWORD=userpassword123 \
  -e MYSQL_DATABASE=my_database \
  -p 3000:3000 \
  mangooer/mysql-mcp-server-sse:latest