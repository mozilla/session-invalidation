BUCKET_NAME="session-invalidation-static-content"

for filename in $(ls static); do
  aws s3 rm "s3://$BUCKET_NAME/$filename";
done
