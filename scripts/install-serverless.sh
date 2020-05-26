if hash serverless 2> /dev/null; then
  echo "serverless already installed";
else
  curl -o- -L https://slss.io/install | bash;
fi
